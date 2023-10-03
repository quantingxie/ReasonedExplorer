import math
import time
import airsim
import networkx as nx
import cv2
from LLM_functions import LLM_checker
from VLM import VLM_query
from utils import *
from simulator_utils import *
import matplotlib.pyplot as plt
import logging
import airsim
from LLM_functions import LLM_evaluator

class Node:
    def __init__(self, Q, id, description, gps, yaw_angle):
        self.id = id  # Unique identifier for the node
        self.Q = Q
        self.score = 0.0
        self.description = description  # Scene description from VLM 
        self.gps = gps  # GPS data
        self.yaw_angle = yaw_angle  # Yaw angle
        self.visited = False  # Whether the node has been visited or not


class Exploration:
    next_node_id = 0
    def __init__(self, exp_name, type, pos, yaw, rrt, k, d0, n, fov, rom, goal):
        self.k = k
        self.d0 = d0
        self.n = n
        self.fov = fov
        self.rom = rom
        self.graph = nx.Graph()
        self.iteration_count = 0
        self.goal = goal
        self.state = {}
        self.nodes = []
        self.exp_name = exp_name
        self.H = [[], [], []]  # Hierarchical abstract
        self.rrt = rrt
        self.frontier_buffer = []
        self.Q_buffer = {}  # Dictionary to store Q-values for nodes
        self.type = type
        self.start_pos = pos
        self.start_yaw = yaw

        logging.basicConfig(filename='exploration.log', level=logging.INFO, format='%(message)s')
        sys.stdout = Logger(experiment_name=exp_name)
        # Initialization for robot control
        self.current_node = None  # Track the current position of the agent
        # initialize simulator
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)

    def adaptive_step_size(self, current_score, min_step, max_step):
        normalized_score = current_score / 5
        return min_step + (1 - normalized_score) * (max_step - min_step)

    def set_start_position(self, position, yaw=None):
        if yaw is None:
            # If no orientation is provided, keep it level (no roll, no pitch, and zero yaw).
            orientation = airsim.to_quaternion(0, 0, 0)  # roll, pitch, yaw in radians
        else:
            print("yaw", yaw)
            orientation = airsim.to_quaternion(0, 0, math.radians(yaw))
            
        pose = airsim.Pose(airsim.Vector3r(*position), orientation)
        self.client.simSetVehiclePose(pose, True)
        
    def cleanup(self):
        # Cleanup and close the connection to AirSim.
        self.client.armDisarm(False)  # Try to disarm the drone
        self.client.enableApiControl(False)
        self.client.reset()
    def draw_path(self, experiment_name: str):
        # Create a directory to save the images if it doesn't exist
        print("Drawing nodes!")
        import os
        
        # Use the provided experiment_number in the directory name
        directory = f"saved_plots/{experiment_name}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Clear the existing plot
        plt.clf()
        
        # Draw nodes and edges
        for node in self.graph.nodes:
            # Draw node as a point
            color = 'pink' if node.visited else 'green'
        
            # Draw node as a point
            plt.scatter(node.gps[1], node.gps[0], color=color)  # Note the swapped coordinates here
        
            # Draw yaw as an arrow (using the node's position and yaw_angle)
            arrow_length = 0.005  # you might want to adjust this for the scale of your graph
            dx = arrow_length * math.sin(math.radians(node.yaw_angle))  # sin for East (from yaw angle)
            dy = arrow_length * math.cos(math.radians(node.yaw_angle))  # cos for North (from yaw angle)
            plt.arrow(node.gps[1], node.gps[0], dx, dy, color='red')  # Note the swapped coordinates here
            if node.score > 0:
                plt.annotate(f"{node.score:.2f}", (node.gps[1], node.gps[0]), textcoords="offset points", xytext=(0,5), ha='center')
                
        # Draw edges between nodes
        for edge in self.graph.edges:
            node1, node2 = edge
            plt.plot([node1.gps[1], node2.gps[1]], [node1.gps[0], node2.gps[0]], color='gray')  # Note the swapped coordinates here

        # Set axis labels
        plt.xlabel("East")
        plt.ylabel("North")
        plt.title(f"Agent's Path with Yaw Directions - Iteration {self.iteration_count}")
        
        # Save the plot
        plt.savefig(f"{directory}/path_iteration_{self.iteration_count}.png")
        
        # Increment the iteration count for next call
        self.iteration_count += 1


    """Methods for graph"""
    def add_node_to_graph(self, Q,  description, gps, yaw_angle):
        node = Node(Q, Exploration.next_node_id, description, gps, yaw_angle)
        Exploration.next_node_id += 1  # Increment the ID for the next node
        self.graph.add_node(node)
        node.visited = False
        return node
        
    def connect_nodes(self, node1, node2):
        weight = self.compute_distance(node1.gps, node2.gps)
        self.graph.add_edge(node1, node2, weight=weight)

    
    def compute_distance(self, pos1, pos2):
        return math.sqrt(sum([(a - b) ** 2 for a, b in zip(pos1, pos2)]))
    
    def shortest_distance_to_frontier(self, start_node, goal_node):
        try:
            # Find the shortest path using Dijkstra's algorithm (considering weights as distances between nodes)
            path = nx.shortest_path(self.graph, source=start_node, target=goal_node, weight='weight')
            return path
        except nx.NetworkXNoPath:
            print("Path does not exist")
            return None

    def explore(self) -> None:
        # Initialize current_node at the beginning of exploration
        step_counter = 0
        self.total_distance = 0
        step_size = 15
        start_position = self.start_pos 
        init_yaw = self.start_yaw
        self.set_start_position(start_position, init_yaw)
        self.stabilize_at_start(start_position, init_yaw)

        initial_gps = get_position(self.client)
        initial_yaw = init_yaw
        self.current_node = self.add_node_to_graph(0, "", initial_gps, initial_yaw)
        self.current_node.visited = True
        total_CT = 0  # Computational Time
        total_TT = 0  # Travel Time

        EXPERIMENT_TYPE = self.type  #Experiment type: RRT, Baseline

        while True:
            current_gps = self.current_node.gps
            current_yaw = self.current_node.yaw_angle
            self.current_node.visited = True
            current_score = self.current_node.Q
            print(current_score)
            step_size = self.adaptive_step_size(current_score, 10, 15) # 5 and 20 for L1 L2 L4
            print(step_size)
            print("GLOBAL STEP: ", step_counter)
            print("Current_Pos", current_gps)
            print("Current_yaw", current_yaw)
            captured_images = get_image(self.client, step_counter, self.exp_name)
            curr_nodes_data = []
            for image in captured_images:
                description = VLM_query(image)
                curr_nodes_data.append((description))

            step_counter += 1

            # Calculate yaw angles and GPS coordinates for each captured image
            nodes = []
            for i, description in enumerate(curr_nodes_data):
                direction = i * (self.rom / (self.n - 1))
                yaw_angle = current_yaw - direction + self.rom / 2  # Adjusting for center of the FOV
                dx = step_size * math.cos(math.radians(yaw_angle))
                dy = step_size * math.sin(math.radians(yaw_angle))
                newX = current_gps[0] + dx
                newY = current_gps[1] + dy

                node = self.add_node_to_graph(0, description, (newX, newY), yaw_angle)
                print("node expanded in ", node.gps, "for angle", node.yaw_angle, "Description", node.description, "\n")
                self.connect_nodes(self.current_node, node)
                nodes.append(node)

            descriptions = [node.description for node in nodes]
            found = False

            if EXPERIMENT_TYPE == "baseline":
                print("Running Baseline")
                for node in nodes:
                    start_time = time.time()
                    node.Q = LLM_evaluator(node.description, goal=self.goal, model="gpt-4")
                    end_time = time.time()
                    CT = end_time - start_time
                    total_CT += CT
                    print("ComputationalT: ", CT, "seconds")

                    check = LLM_checker(node.description, self.goal, model="gpt-4")
                    print("Goal Found? ", check)
                    if check.strip() == "Yes":
                        print("!!! Found GOAL !!!")
                        self.client.hoverAsync().join()
                        found = True
                        break

            elif EXPERIMENT_TYPE == "RRT":
                print("Running RRT")
                start_time = time.time()
                self.rrt.run_rrt(descriptions)
                end_time = time.time()
                CT = end_time - start_time
                total_CT += CT
                print("ComputationalT: ", CT, "seconds")
                print("User-Instructions: ", self.goal)
                for node in nodes:
                    node.Q = self.rrt.Q.get(str(node.description), 0)
                    check = LLM_checker(node.description, self.goal, model="gpt-4")
                    print("Goal Found? ", check)
                    if check.strip() == "Yes" or check.strip() == "yes":
                        print("!!! Found GOAL !!!")
                        self.client.hoverAsync().join()
                        found = True
                        break

            if found:
                break

            self.frontier_buffer.extend(nodes)

            action_start_time = time.time()
            self.action(self.k, self.d0)
            action_end_time = time.time()
            TT = action_end_time - action_start_time
            print("TravelT: ", TT, "seconds")

            total_TT += TT
            print("Total TravelT", total_TT)
            print("Total ComputationalT", total_CT)
            print("Total Distance Traveled: ", self.total_distance)

            
    """Methods for robot movement"""
    def action(self, k, d0) -> None:
        """Chooses and executes an action based on the Q-values."""
        import math  # Ensure you've imported the math library

        # Compute distances to frontier nodes using Euclidean distance
        current_node_gps = get_position(self.client)
        print("Curret GPS",current_node_gps)
        nodes_gps_list = [node.gps for node in self.graph.nodes if not node.visited]

        d_values = compute_euclidean_distances_from_current_sim(current_node_gps, nodes_gps_list)
        print("d values", d_values)

        # Calculate sigmoid-modulated distances for each node
        sigma_values = [sigmoid_modulated_distance(d, k, d0) for d in d_values]
        print("Sigma values", sigma_values)

        # Score nodes based on Q-value adjusted by sigmoid-modulated distance
        unvisited_nodes = [node for node in self.graph.nodes if not node.visited]
        scores = [(node, node.Q - sigma_values[nodes_gps_list.index(node.gps)]) for node in unvisited_nodes]
        print("SCORES", scores)

        self.chosen_node = max(scores, key=lambda x: x[1])[0]
        for node, score in scores:
            node.score = score

        distance_to_next_point = math.sqrt((self.chosen_node.gps[0] - current_node_gps[0])**2 + (self.chosen_node.gps[1] - current_node_gps[1])**2)
        self.total_distance += distance_to_next_point  # Accumulate distance
        self.chosen_node.visited = True
        self.draw_path(self.exp_name)

        # Make the robot move to the chosen node's location
        self.move_to_next_point(next_position=self.chosen_node.gps, desired_yaw=self.chosen_node.yaw_angle, current_yaw = self.current_node.yaw_angle)

        self.current_node = self.chosen_node
        self.current_node.visited = True

    def move_to_next_point(self, next_position, desired_yaw, current_yaw):
        # Convert the lat-long into NED format (if they aren't already)
        x, y = next_position
        z = -1
        self.client.moveToPositionAsync(x, y, z, 1, yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=desired_yaw)).join()

        time.sleep(5)


    def stabilize_at_start(self, start_pos, start_yaw):
        # This will ensure the drone stabilizes at the position it starts at
        self.client.moveToPositionAsync(start_pos[0], start_pos[1], -1, 3, 
                                        yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=start_yaw)).join()
        time.sleep(2)
        self.client.hoverAsync().join()

import sys
class Logger(object):
    def __init__(self, experiment_name="Default"):
        self.terminal = sys.stdout
        
        # Construct filename based on experiment name
        self.filename = f"{experiment_name}.log"
        
        self.log = open(self.filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        pass   
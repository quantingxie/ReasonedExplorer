import math
import time
import airsim
import networkx as nx
import cv2
from typing import List, Tuple
from LLM_functions import LLM_abstractor, LLM_rephraser, LLM_checker
from VLM import VLM_query
from utils import *
from simulator_utils import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import logging
from LLM_functions import LLM_evaluator

class Node:
    def __init__(self, Q, id, description, gps, yaw_angle):
        self.id = id  # Unique identifier for the node
        self.Q = Q
        self.score = 0.0
        self.description = description  # Scene description from VLM or LLM_rephraser
        self.gps = gps  # GPS data
        self.yaw_angle = yaw_angle  # Yaw angle
        self.visited = False  # Whether the node has been visited or not


class Exploration:
    next_node_id = 0
    def __init__(self, mcts, x, k, n, fov, rom, goal, model):
        self.x = x
        self.k = k
        self.n = n
        self.fov = fov
        self.rom = rom
        self.graph = nx.Graph()
        self.iteration_count = 0
        self.goal = goal
        self.model = model
        self.state = {}
        self.nodes = []
        self.H = [[], [], []]  # Hierarchical abstract
        self.mcts = mcts
        self.frontier_buffer = []
        self.Q_buffer = {}  # Dictionary to store Q-values for nodes
        logging.basicConfig(filename='exploration.log', level=logging.INFO, format='%(message)s')
        sys.stdout = Logger("my_output2.log")
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
            print("!!yaw", yaw)
            orientation = airsim.to_quaternion(0, 0, math.radians(yaw))
            
        pose = airsim.Pose(airsim.Vector3r(*position), orientation)
        self.client.simSetVehiclePose(pose, True)
        
    def cleanup(self):
        # Cleanup and close the connection to AirSim.
        self.client.armDisarm(False)  # Try to disarm the drone
        self.client.enableApiControl(False)
        self.client.reset()
    def draw_path(self):
        # Create a directory to save the images if it doesn't exist
        print("Drawing nodes...!!!!!!!!!!!!!!!!!!!!!!!!!")
        import os
        directory = "saved_plots"
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

    def compute_distance(self, gps1, gps2):
        # Compute distance between two GPS points (you can use the provided conversion functions)
        # This is just a placeholder; replace it with an appropriate function
        lat_diff = gps2[0] - gps1[0]
        lon_diff = gps2[1] - gps1[1]
        lat_distance = lat_to_meters(lat_diff)
        lon_distance = lon_to_meters(lon_diff, gps1[0])
        return math.sqrt(lat_distance**2 + lon_distance**2)
    
    def shortest_distance_to_frontier(self, start_node, goal_node):
        try:
            # Find the shortest path using Dijkstra's algorithm (considering weights as distances between nodes)
            path = nx.shortest_path(self.graph, source=start_node, target=goal_node, weight='weight')
            return path
        except nx.NetworkXNoPath:
            print("Path does not exist")
            return None
    
    """Methods for hierachycal tree"""
    def abstract(self, n: List, l: int) -> None:
        """Recursively creates abstract representations of nodes."""
        if l <= 2 and len(n) == self.x:
            S_l = LLM_abstractor(n, model=self.model)
            n.clear()
            self.H[l].append(S_l)
            self.abstract(self.H[l], l+1)

    def explore(self) -> None:
        # Initialize current_node at the beginning of exploration
        step_counter = 0
        step_size = 15
        start_position = (15, -44, -5)  # Example NED position (N, E, D)
        init_yaw = 0  # Example orientation (roll, pitch, yaw)
        self.set_start_position(start_position, init_yaw)
        self.stabilize_at_start()
        # self.takeoff()

        initial_gps = get_position(self.client)
        initial_yaw = init_yaw
        self.current_node = self.add_node_to_graph(0, "", initial_gps, initial_yaw)
        self.current_node.visited = True

        while True:
            # current_gps = get_position(self.client)  # Fetching the current position and yaw of the agent
            # current_yaw = get_yaw(self.client)

            current_gps = self.current_node.gps
            current_yaw = self.current_node.yaw_angle
            self.current_node.visited = True
            current_score = self.current_node.Q
            print(current_score)
            step_size = self.adaptive_step_size(current_score, 5, 20)
            print(step_size)
            # self.current_node = self.add_node_to_graph(0, "", current_gps, current_yaw)
            print("GLOBAL STEP: ", step_counter)
            print("Current_Pos", current_gps)
            print("Current_yaw", current_yaw)
            captured_images = get_image(self.client, step_counter)
            curr_nodes_data = []
            for image in captured_images:
                description = VLM_query(image)
                curr_nodes_data.append((description))


            step_counter += 1
            # Calculate yaw angles and GPS coordinates for each captured image
            nodes = []
            for i, description in enumerate(curr_nodes_data):
                direction = i * (self.rom / (self.n - 1))

                # Incorporating the actual yaw into the calculated yaw angle
                yaw_angle = current_yaw - direction + self.rom/2  # Adjusting for center of the FOV

                # print("Yaw_angle", yaw_angle)
                dx = step_size * math.cos(math.radians(yaw_angle))
                dy = step_size * math.sin(math.radians(yaw_angle))

                newX = current_gps[0] + dx
                newY = current_gps[1] + dy
              
                node = self.add_node_to_graph(0, description, (newX, newY), yaw_angle)
                print("node expanded in ", node.gps, "for angle", node.yaw_angle, "Description", node.description, "\n")
                self.connect_nodes(self.current_node, node)
                nodes.append(node)

            # S_0 = LLM_abstractor([node.description for node in nodes], model=self.model)
            # print("abstracted base nodes")
            # self.H[0].append(S_0)
            # print("abstracted top nodes")
            # self.abstract(self.H[0], 1)
            # G = [h[-1] for h in self.H if h]
            # # Use LLM_rephraser to get new descriptions for nodes
            # rephrased_nodes = []
            # for node in nodes:

            #     rephrased_node = LLM_rephraser(node.description, G, model=self.model)

            #     rephrased_nodes.append(rephrased_node)

            # logging.info("expaned nodes rephrased")
            # print("expaned nodes rephrased")

            # for i, node in enumerate(nodes):
            #     node.description = rephrased_nodes[i]

            # logging.info("Running MCTS")
            print("Running MCTS")
            descriptions = [node.description for node in nodes]
            # self.mcts.run_mcts(self.k, descriptions) # MCTS real
            found = False

            #Baseline 1
            # naiveLLM_start_time = time.time()
            # for node in nodes:
            #     print(self.goal)
            #     print("Node Description", node.description)
            #     node.Q = LLM_evaluator(node.description, goal=self.goal, model="gpt-4")
            #     print("NodeQ:", node.Q)
            #     check = LLM_checker(node.description, self.goal, model="gpt-4")

            #     print("Goal Found? ", check)
            #     if check.strip() == "Yes":
            #         print("!!! Found GOAL !!!")
            #         self.client.hoverAsync().join()
            #         found = True
            #         break
            # if found:
            #     break
            # naiveLLM_end_time = time.time()
            # print("NaiveLLM thinking time: ", naiveLLM_end_time - naiveLLM_start_time, "seconds")

            # MCTS
            mcts_start_time = time.time()
            self.mcts.run_mcts(descriptions)
            mcts_end_time = time.time()
            print("MCTS thinking time: ", mcts_end_time - mcts_start_time, "seconds")

            print("User-Instructions: ", self.goal)
            for node in nodes:
                node.Q = self.mcts.Q.get(str(node.description), 0)
                
                check = LLM_checker(node.description, self.goal, model="gpt-4")
                print("Goal Found? ", check)
                if check.strip() == "Yes":
                    print("!!! Found GOAL !!!")
                    self.client.hoverAsync().join()
                    found = True
                    break
            if found:
                break

            self.frontier_buffer.extend(nodes)

            action_start_time = time.time()
            self.action()
            action_end_time = time.time()
            print("Action time: ", action_end_time - action_start_time, "seconds")


    """Methods for robot movement"""
    def action(self) -> None:
        """Chooses and executes an action based on the Q-values."""
        # Compute distances to frontier nodes using Euclidean distance
        current_node_gps = get_position(self.client)
        print("Curret GPS",current_node_gps)
        nodes_gps_list = [node.gps for node in self.graph.nodes if not node.visited] # changes
        # nodes_gps_list = [node.gps for node in self.frontier_buffer]

        # nodes_gps_list = [data['position'] for data in self.Q_buffer.values()]
        d_values = compute_euclidean_distances_from_current(current_node_gps, nodes_gps_list)
        print("d values", d_values)
        # Select node with the highest Q-value adjusted by distance
        # self.chosen_node = max(self.nodes, key=lambda node: self.Q_buffer[str(node.id)] / d_values[self.nodes.index(node)])

        unvisited_nodes = [node for node in self.graph.nodes if not node.visited] # changes
        # if unvisited_nodes:
        #     unvisited_ids = [node.id for node in unvisited_nodes]
        #     print("Unvisited Nodes ids:", unvisited_ids)

        scores = [(node, node.Q -  0*d_values[nodes_gps_list.index(node.gps)]) for node in unvisited_nodes] # changes unvisited_nodes
        print("SCORES", scores)
        self.chosen_node = max(scores, key=lambda x: x[1])[0]
        for node, score in scores:
            node.score = score

        # print(f"Before update, chosen_node visited status: {self.chosen_node.visited}")
        self.chosen_node.visited = True
        # print(f"Node Identity: {id(self.chosen_node)}")
        # print(f"After update, chosen_node visited status: {self.chosen_node.visited}")
        self.draw_path()


        # Make the robot move to the chosen node's location

        self.move_to_next_point(next_position=self.chosen_node.gps, desired_yaw=self.chosen_node.yaw_angle, current_yaw = self.current_node.yaw_angle)
        # self.client.rotateByYawRateAsync(self.chosen_node.yaw_angle, 1)

        # Update the current node to be the chosen node
        # self.chosen_node.visited = True
        self.current_node = self.chosen_node
        self.current_node.visited = True
        # del self.Q_buffer[str(self.chosen_node.id)]
        # self.frontier_buffer.remove(self.current_node)


    def move_to_next_point(self, next_position, desired_yaw, current_yaw):
        # Convert the lat-long into NED format (if they aren't already)
        x, y = next_position
        z = -1
        self.client.moveToPositionAsync(x, y, z, 1, yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=desired_yaw)).join()
        # self.moveToPosition(x, y, z, 1)

        time.sleep(5)
        # self.client.hoverAsync().join()


    def stabilize_at_start(self):
        # This will ensure the drone stabilizes at the position it starts at
        self.client.moveToPositionAsync(15, -44, -1, 3, yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0)).join()
        time.sleep(2)
        self.client.hoverAsync().join()

    # def moveToPosition(self, x, y, z, v):
    #     currentPos = self.client.getMultirotorState().kinematics_estimated.position
    #     t = ((currentPos.x_val - x)**2 + (currentPos.y_val - y)**2 + (currentPos.z_val - z)**2)**0.5 / v
    #     delta_x = x - currentPos.x_val
    #     delta_y = y - currentPos.y_val
    #     delta_z = z - currentPos.z_val
    #     vx = delta_x / t
    #     vy = delta_y / t
    #     vz = delta_z / t
    #     self.client.moveByVelocityAsync(vx, vy, vz, t)
    #     time.sleep(t)
    #     self.client.moveByVelocityAsync(0, 0, 0, 5)
    #     self.client.hoverAsync().join()
    # def takeoff(self):
    #     self.client.armDisarm(True)
    #     self.client.takeoffAsync().join()
import sys
class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        pass    
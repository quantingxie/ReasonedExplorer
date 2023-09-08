import math
import time
import airsim
import networkx as nx
import cv2
from typing import List, Tuple
from LLM_functions import LLM_abstractor, LLM_rephraser
from VLM import VLM_query
from utils import *
from simulator_utils import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from LLM_functions import LLM_evaluator
class Node:
    def __init__(self, description, gps, yaw_angle):
        self.description = description  # Scene description from VLM or LLM_rephraser
        self.gps = gps  # GPS data
        self.yaw_angle = yaw_angle  # Yaw angle

class Exploration:
    def __init__(self, mcts, x, k, n, fov, rom, model):
        self.x = x
        self.k = k
        self.n = n
        self.fov = fov
        self.rom = rom
        self.graph = nx.Graph()
        self.iteration_count = 0

        self.model = model
        self.state = {}
        self.nodes = []
        self.H = [[], [], []]  # Hierarchical abstract
        self.mcts = mcts
        self.Q_list = {}  # Dictionary to store Q-values for nodes

        # Initialization for robot control
        self.current_node = None  # Track the current position of the agent
        print("Test")
        # initialize simulator
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)
        self.car_controls = airsim.CarControls()

    def cleanup(self):
        # Cleanup and close the connection to AirSim.
        self.client.armDisarm(False)  # Try to disarm the drone
        self.client.enableApiControl(False)
        self.client.reset()
    def draw_path(self):
        # Create a directory to save the images if it doesn't exist
        import os
        directory = "saved_plots"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Clear the existing plot
        plt.clf()
        
        # Draw nodes and edges
        for node in self.graph.nodes:
            # Draw node as a point
            plt.scatter(node.gps[0], node.gps[1], color='blue')
            
            # Draw yaw as an arrow (using the node's position and yaw_angle)
            arrow_length = 0.005  # you might want to adjust this for the scale of your graph
            dx = arrow_length * math.cos(math.radians(node.yaw_angle))
            dy = arrow_length * math.sin(math.radians(node.yaw_angle))
            plt.arrow(node.gps[0], node.gps[1], dx, dy, color='red')
            
        # Draw edges between nodes
        for edge in self.graph.edges:
            node1, node2 = edge
            plt.plot([node1.gps[0], node2.gps[0]], [node1.gps[1], node2.gps[1]], color='gray')

        # Set axis labels
        plt.xlabel("Latitude")
        plt.ylabel("Longitude")
        plt.title(f"Agent's Path with Yaw Directions - Iteration {self.iteration_count}")
        
        # Save the plot
        plt.savefig(f"{directory}/path_iteration_{self.iteration_count}.png")
        
        # Increment the iteration count for next call
        self.iteration_count += 1

    """Methods for graph"""
    def add_node_to_graph(self, description, gps, yaw_angle):
        node = Node(description, gps, yaw_angle)
        self.graph.add_node(node)
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
        initial_gps = get_position(self.client)
        initial_yaw = 0
        self.current_node = self.add_node_to_graph("", initial_gps, initial_yaw)
        self.takeoff()
        while True:
            current_gps = get_position(self.client)  # Fetching the current position and yaw of the agent
            current_yaw = get_yaw(self.client)
            print("Current_Pos", current_gps)
            print("Current_yaw", current_yaw)
            captured_images = get_image(self.client)
            curr_nodes_data = []
            reached_goal = False
            for image in captured_images:
                description, found = VLM_query(image)
                curr_nodes_data.append((description, found))
                if found:
                    reached_goal=True
            if reached_goal:
                break

            # Calculate yaw angles and GPS coordinates for each captured image
            nodes = []
            for i, (description, _) in enumerate(curr_nodes_data):
                direction = i * (self.rom / (self.n -1))

                # Incorporating the actual yaw into the calculated yaw angle
                yaw_angle = current_yaw + direction - self.rom/2  # Adjusting for center of the FOV
                print("Yaw_angle", yaw_angle)
                dx = 20 * math.cos(math.radians(yaw_angle))
                dy = 20 * math.sin(math.radians(yaw_angle))
                print("COS",math.cos(yaw_angle))
                print(dx, dy)
                # delta_lat = meters_to_lat(dy)
                # delta_lon = meters_to_lon(dx, current_gps[0])

                new_lat = current_gps[0] + dx
                new_lon = current_gps[1] + dy

                node = self.add_node_to_graph(description, (new_lat, new_lon), yaw_angle)
                print("node expanded")
                self.connect_nodes(self.current_node, node)
                nodes.append(node)

            self.nodes = nodes

            print("Running")
            descriptions = [node.description for node in nodes]
            scores=[]
            for i in range(len(descriptions)):
                scores.append((i,LLM_evaluator(descriptions[i], goal=self.mcts.goal,model=self.model)))
            max_node = nodes[max(scores, key=lambda x: x[1])[0]]
            self.action(max_node)

    """Methods for robot movement"""
    def action(self, max_node) -> None:
        """Chooses and executes an action based on the Q-values."""
        # Compute distances to frontier nodes using Euclidean distance
        # Select node with the highest Q-value adjusted by distance
        self.chosen_node = max_node
        # Remove the chosen node from the list of unexplored nodes to prevent revisiting it in future iterations
        self.nodes.remove(self.chosen_node)
        # Make the robot move to the chosen node's location
        self.move_to_next_point(next_position=self.chosen_node.gps, desired_yaw=self.chosen_node.yaw_angle, current_yaw = self.current_node.yaw_angle)
        # Update the current node to be the chosen node
        self.current_node = self.chosen_node
        del self.Q_list[str(self.chosen_node)]
        self.draw_path()

    # def move_to_next_point(self, next_position, desired_yaw, current_yaw):
    #     # Convert the lat-long into NED format (if they aren't already)
    #     x, y = next_position # You'd need to define this conversion function
    #     z = - 0.2
    #     # Move to the target position
    #     self.client.moveToPositionAsync(x, y, z, 2).join()  # Velocity = 3
        
    #     # Now, change the yaw to face the desired direction
    #     yaw_rate = 15  # Set a yaw rate (degrees per second)

    #     duration = abs(desired_yaw-current_yaw) / yaw_rate
        
    #     yaw_error = desired_yaw - current_yaw
    #     self.client.rotateByYawRateAsync(yaw_rate if yaw_error > 0 else -yaw_rate, abs(duration)).join()
        
    #     # Make sure the drone hovers after moving
    #     self.client.hoverAsync().join()
    def move_to_next_point(self, next_position, desired_yaw, current_yaw):
        # Convert the lat-long into NED format (if they aren't already)
        x, y = next_position
        z = -0.2

        # Move to the target position and set yaw
        self.client.moveToPositionAsync(x, y, z, 3, yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=desired_yaw)).join()
        print("Current Yaw", current_yaw)
        print("Desired Yaw", desired_yaw)
        # Make sure the drone hovers after moving
        self.client.hoverAsync().join()


    def takeoff(self):
        self.client.armDisarm(True)
        self.client.takeoffAsync().join()

# def calculate_velocity_yaw(current_pos, current_yaw, waypoint, desired_node_yaw):
#     Kp_yaw = 0.4
#     Ki_yaw = 0.2
#     Kd_yaw = 0.02
#     EPSILON = 1e-6
#     position_error = haversine_distance(current_pos, waypoint)
#     dlat = waypoint[0] - current_pos[0]
#     dlon = waypoint[1] - current_pos[1]

#     if position_error > 1:  # If the robot is further than 1 unit from the waypoint
#         desired_yaw = math.atan2(dlat, dlon)
#         desired_yaw = desired_yaw - np.pi/2 
#     else:
#         desired_yaw = desired_node_yaw  # Set desired yaw to the node's yaw as the robot gets closer

#     desired_yaw = (desired_yaw + np.pi) % (2 * np.pi) - np.pi

#     yaw_error = desired_yaw - current_yaw
#     yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
    
#     yaw_integral = 0  # Initialize this in your global scope if you want integral action
#     previous_yaw_error = 0  # Initialize this in your global scope

#     dt = 0.01  # Consider adjusting this as per your needs
#     yaw_integral += yaw_error * dt
#     yaw_derivative = (yaw_error - previous_yaw_error) / (dt + EPSILON)
#     yaw_speed = Kp_yaw * yaw_error + Ki_yaw * yaw_integral + Kd_yaw * yaw_derivative
#     return yaw_speed, yaw_error, position_error, desired_yaw




import math
import networkx as nx
import cv2
from typing import List, Tuple
from LLM_functions import LLM_abstractor, LLM_rephraser
from VLM import VLM_query
from utils import *
from robot_utils import *

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

        self.model = model
        self.state = {}
        self.nodes = []
        self.H = [[], [], []]  # Hierarchical abstract
        self.mcts = mcts
        self.Q_list = {}  # Dictionary to store Q-values for nodes

        # Initialization for robot control
        self.current_node = None  # Track the current position of the agent
        self.HIGHLEVEL = 0xee
        self.udp = sdk.UDP(self.HIGHLEVEL, 8080, "192.168.123.161", 8082)
        self.cmd = sdk.HighCmd()
        self.state = sdk.HighState()
        self.udp.InitCmdData(self.cmd)

        threading.Thread(target=socket_client_thread, daemon=True).start()  # Start the socket client thread for fetching GPS data


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
        initial_gps, initial_yaw = get_GPS()
        self.current_node = self.add_node_to_graph("", initial_gps, initial_yaw)
        
        while True:
            current_gps, current_yaw = get_GPS()  # Fetching the current position and yaw of the agent
            
            captured_images = self.capture_images_by_rotate(self.n, self.rom)

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
                direction = math.radians(i * (self.rom / self.n))
                dx = 5 * math.cos(direction)
                dy = 5 * math.sin(direction)
                
                delta_lat = meters_to_lat(dy)
                delta_lon = meters_to_lon(dx, current_gps[0])

                new_lat = current_gps[0] + delta_lat
                new_lon = current_gps[1] + delta_lon

                # Incorporating the actual yaw into the calculated yaw angle
                yaw_angle = current_yaw + direction - self.rom  # Adjusting for center of the FOV

                node = self.add_node_to_graph(description, (new_lat, new_lon), yaw_angle)
                print("node expanded")
                self.connect_nodes(self.current_node, node)
                nodes.append(node)

            S_0 = LLM_abstractor([node.description for node in nodes], model=self.model)
            print("abstracted base nodes")
            self.H[0].append(S_0)
            print("abstracted top nodes")
            self.abstract(self.H[0], 1)
            G = [h[-1] for h in self.H if h]

            # Use LLM_rephraser to get new descriptions for nodes
            rephrased_nodes = [LLM_rephraser(node.description, G, model=self.model) for node in nodes]
            print("expaned nodes rephrased")

            for i, node in enumerate(nodes):
                node.description = rephrased_nodes[i]

            print("Running MCTS")
            descriptions = [node.description for node in nodes]
            self.mcts.run_mcts(self.k, descriptions)

            for node in nodes:
                self.Q_list[str(node)] = self.mcts.Q.get(str(node.description), 0)
                
            self.action()

    """Methods for robot movement"""
    def action(self) -> None:
        """Chooses and executes an action based on the Q-values."""
        # Compute distances to frontier nodes using Euclidean distance
        current_node_gps = self.current_node.gps
        nodes_gps_list = [node.gps for node in self.nodes]
        d_values = compute_euclidean_distances_from_current(current_node_gps, nodes_gps_list)
        
        # Select node with the highest Q-value adjusted by distance
        self.chosen_node = max(self.nodes, key=lambda node: self.Q_list[str(node.description)] / d_values[self.nodes.index(node)])

        # Remove the chosen node from the list of unexplored nodes to prevent revisiting it in future iterations
        self.nodes.remove(self.chosen_node)

        # Make the robot move to the chosen node's location
        self.move_to_next_point(next_position=self.chosen_node.gps, desired_yaw=self.chosen_node.yaw_angle)

        # Update the current node to be the chosen node
        self.current_node = self.chosen_node
        del self.Q_list[str(self.chosen_node.description)]


    def capture_images_by_rotate(self, n: int, range_of_motion=20) -> list:
        captured_images = []

        # Convert range_of_motion to radians
        range_of_motion_radians = math.radians(range_of_motion)

        # Calculate min_angle based on range_of_motion in radians
        min_angle = -range_of_motion_radians / 2

        # Calculate the angle increment in radians
        angle_increment = range_of_motion_radians / n

        # Initialize motion time and yaw angle
        motiontime = 0
        yaw_angle = min_angle

        while motiontime < n:
            time.sleep(0.005)
            motiontime += 1

            # Receive current state (Not necessary for your function, but kept for compatibility)
            self.udp.Recv()
            self.udp.GetRecv(self.state)

            # Set mode and euler angles for the robot
            self.cmd.mode = 1
            self.cmd.euler = [0, 0, yaw_angle]

            # Send the udp command
            self.udp.SetSend(self.cmd)
            self.udp.Send()

            # Capture image and append it if it's not None
            angle_in_degrees = math.degrees(yaw_angle)
            image = capture_image_at_angle(angle_in_degrees)
            if image is not None:
                captured_images.append(image)

            # Update the yaw_angle for the next iteration
            yaw_angle += angle_increment

        return captured_images

    def move_to_next_point(self, next_position, desired_yaw):

        try:
            while True:
                self.udp.Recv()
                self.udp.GetRecv(self.state)

                dt = 0.01
                current_pos = get_GPS()
                raw_yaw = get_yaw()
                current_yaw = next(raw_yaw)
                
                self.cmd.mode = 2
                self.cmd.gaitType = 1
                self.cmd.bodyHeight = 0.1

                v, y, yaw_error, previous_yaw_error, _, _ = calculate_velocity_yaw(current_pos, current_yaw, next_position, desired_yaw)
                self.cmd.velocity = [v, 0]
                self.cmd.yawSpeed = y

                self.udp.SetSend(self.cmd)
                self.udp.Send()

                # Break condition: If the robot is close to next_position
                if haversine_distance(current_pos, next_position) < 1:
                    break

        except Exception as e:
            print(f"Error occurred in the control loop: {e}")
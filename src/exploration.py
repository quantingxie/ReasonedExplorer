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

        self.current_node = None  # Track the current position of the agent
        threading.Thread(target=socket_client_thread, daemon=True).start() # Start the socket client thread for fetching GPS data


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

    def is_goal_reached(self, bounding_boxes: List[Tuple[int, int, int, int]]) -> bool:
        screen_area = 384 * 384
        for box in bounding_boxes:
            x1, y1, x2, y2 = box
            box_area = (x2 - x1) * (y2 - y1)
            if box_area >= 0.5 * screen_area:
                return True
        return False

    def explore(self) -> None:
        # Initialize current_node at the beginning of exploration
        initial_gps, initial_yaw = get_GPS()
        self.current_node = self.add_node_to_graph("", initial_gps, initial_yaw)
        
        while True:
            current_gps, current_yaw = get_GPS()  # Fetching the current position and yaw of the agent
            
            # Capture images at different angles using the integrated function
            captured_images = capture_images_by_rotate(self.n, self.rom)

            # Process the captured images to get their descriptions and bounding boxes
            curr_nodes_data = []
            for image in captured_images:
                description, bbox = VLM_query(image)
                print("VLM set")  
                curr_nodes_data.append((description, bbox))
            
            if self.is_goal_reached([bbox for _, bbox in curr_nodes_data]):
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
        move_to_next_point(current_position=current_node_gps, next_position=self.chosen_node.gps)

        # Update the current node to be the chosen node
        self.current_node = self.chosen_node
        del self.Q_list[str(self.chosen_node.description)]

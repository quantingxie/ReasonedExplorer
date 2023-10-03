import math
import time
import networkx as nx
import cv2
from LLM_functions import LLM_checker
from VLM import VLM_query
from utils import *
import logging
from LLM_functions import LLM_evaluator
import robot_interface as sdk

MY_API_KEY = "" # Google API key

def capture_image_at_angle(angle, step_number):
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return
    
    ret, frame = camera.read()
    frame = cv2.flip(frame, 0)
    frame = cv2.flip(frame, 1)

    filename = f"step_{step_number}_angle_{angle:.1f}_degrees.jpg"
    cv2.imwrite(filename, frame)

    if not ret:
        print(f"Error: Couldn't capture image at angle {angle:.1f} during step {step_number}.")
        return None

    return filename

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
    def __init__(self, exp_name, type, gps, yaw, rrt, k, d0, n, fov, rom, goal):
        self.k = k
        self.d0 = d0
        self.n = n
        self.fov = fov
        self.rom = rom
        self.graph = nx.Graph()
        self.iteration_count = 0
        self.goal = goal
        self.state = {}
        self.type = type
        self.nodes = []
        self.H = [[], [], []]  # Hierarchical abstract
        self.rrt = rrt
        self.exp_name = exp_name
        self.frontier_buffer = []
        self.step_counter = 0
        self.Q_buffer = {}  # Dictionary to store Q-values for nodes
        logging.basicConfig(filename='exploration.log', level=logging.INFO, format='%(message)s')
        sys.stdout = Logger(experiment_name=exp_name)
        # Initialization for robot control
        self.current_node = None  # Track the current position of the agent
        # initialize simulator
        # Initialization for robot control
        self.current_node = None  # Track the current position of the agent
        self.HIGHLEVEL = 0xee
        self.udp = sdk.UDP(self.HIGHLEVEL, 8080, "192.168.123.161", 8082)
        self.cmd = sdk.HighCmd()
        self.state = sdk.HighState()
        self.udp.InitCmdData(self.cmd)

        # self.initial_gps = 40.444704, -79.947455 #TCS
        # self.initial_gps = 40.441975, -79.940444 # basket ball
        # self.initial_gps = 40.4420659, -79.9402534 # find bench
        # self.initial_gps = 40.4420299, -79.9392677 # soccer field
        self.initial_gps = gps
        self.initial_yaw = yaw


    def adaptive_step_size(self, current_score, min_step, max_step):
        normalized_score = current_score / 5
        return min_step + (1 - normalized_score) * (max_step - min_step)


    def draw_path(self, initial_gps, filename_prefix="path_map.html"):
        # Assuming each node has gps_data as (lat, lon)
        lat0, lon0 = initial_gps

        gmap_graph = gmplot.GoogleMapPlotter(lat0, lon0, 19)
        gmap_graph.apikey = MY_API_KEY
        gmap_graph.map_type = "satellite"

        # Add nodes to the map
        for node in self.graph.nodes:
            color = 'green' if node.visited else 'red'
            gmap_graph.circle(node.gps[0], node.gps[1], 0.5, color=color)
            
            # Annotate score if present
            if hasattr(node, 'score') and node.score > -1:
                gmap_graph.marker(node.gps[0], node.gps[1], title=f"{node.score:.2f}")

        # Add connections (edges) between nodes
        for edge in self.graph.edges:
            node1, node2 = edge
            gmap_graph.plot([node1.gps[0], node2.gps[0]], [node1.gps[1], node2.gps[1]], 'blue', edge_width=2.5)

        # Save the map to an HTML file
        filename = f"{filename_prefix}_step_{self.iteration_count}.html"
        gmap_graph.draw(filename)

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
        lat_diff = gps2[0] - gps1[0]
        lon_diff = gps2[1] - gps1[1]
        lat_distance = lat_to_meters(lat_diff)
        lon_distance = lon_to_meters(lon_diff, gps1[0])
        return math.sqrt(lat_distance**2 + lon_distance**2)
    

    def explore(self) -> None:
        # Initialize current_node at the beginning of exploration

        self.current_node = self.add_node_to_graph(0, "", self.initial_gps, self.initial_yaw)
        self.current_node.visited = True
        EXPERIMENT_TYPE = self.type  #Experiment type: RRT, MCTS, Baseline
        total_CT = 0
        total_TT = 0
        while True:

            current_gps = self.current_node.gps
            current_yaw = self.current_node.yaw_angle
            self.current_node.visited = True
            current_score = self.current_node.Q
            step_size = self.adaptive_step_size(current_score, 2e-5, 3.5e-5)
            print(step_size)
            print("GLOBAL STEP: ", self.step_counter)
            print("Current_Pos", current_gps)
            print("Current_yaw", current_yaw)
            captured_images = self.capture_images_by_rotate(self.n, self.rom)
            curr_nodes_data = []
            print("querying VLM")
            for image in captured_images:
                description = VLM_query(image)
                curr_nodes_data.append((description))

            print("complete")
            self.step_counter += 1
            # Calculate yaw angles and GPS coordinates for each captured image
            nodes = []
            for i, description in enumerate(curr_nodes_data):
                direction = i * (120 / (self.n - 1))

                # Incorporating the actual yaw into the calculated yaw angle
                yaw_angle = current_yaw - direction + 60  # Adjusting for center of the FOV

                print("Yaw_angle", yaw_angle)
                dx = step_size * math.cos(math.radians(yaw_angle))
                dy = step_size * math.sin(math.radians(yaw_angle))

                newlat = current_gps[0] + dy
                newlon = current_gps[1] - dx
              
                node = self.add_node_to_graph(0, description, (newlat, newlon), yaw_angle)
                print("node expanded in ", node.gps, "for angle", node.yaw_angle, "Description", node.description, "\n")
                self.connect_nodes(self.current_node, node)
                nodes.append(node)

       
            descriptions = [node.description for node in nodes]
            # self.mcts.run_mcts(self.k, descriptions) # MCTS real
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
                    if check.strip() == "Yes":
                        print("!!! Found GOAL !!!")
                        self.client.hoverAsync().join()
                        found = True
                        break

            if found:
                break

            action_start_time = time.time()
            self.action()
            action_end_time = time.time()
            TT = action_end_time - action_start_time
            print("TravelT: ", TT, "seconds")

            total_TT += TT
            print("Total TravelT", total_TT)
            print("Total ComputationalT", total_CT)


    """Methods for robot movement"""
    def action(self) -> None:
        """Chooses and executes an action based on the Q-values."""
        # Compute distances to frontier nodes using Euclidean distance

        nodes_gps_list = [node.gps for node in self.graph.nodes if not node.visited] # changes

        d_values = compute_euclidean_distances_from_current(self.current_node.gps, nodes_gps_list)
        print("d values", d_values)

        unvisited_nodes = [node for node in self.graph.nodes if not node.visited] # changes
 
        scores = [(node, node.Q -  0*d_values[nodes_gps_list.index(node.gps)]) for node in unvisited_nodes] # changes unvisited_nodes
        print("SCORES", scores)
        self.chosen_node = max(scores, key=lambda x: x[1])[0]
        for node, score in scores:
            node.score = score
        self.chosen_node.visited = True

        self.draw_path(self.initial_gps, self.exp_name)

        print("Press 'enter' to start the action and 'enter again' to end the action.")

        # Wait for the 's' key to be pressed to start the action
        input()
        print("Starting the action...") 

        input()
        print("Action completed.")

        self.current_node = self.chosen_node
        self.current_node.visited = True


    def capture_images_by_rotate(self, n: int, range_of_motion=20) -> list:
        captured_images = []

        motiontime = 0
        while True:
            time.sleep(0.002)
            motiontime = motiontime + 1
            self.udp.Recv()
            self.udp.GetRecv(self.state)
                             
            if(motiontime > 0 and motiontime < 1000):
                self.cmd.mode = 2
                self.cmd.yawSpeed = -0.255433

            if(motiontime > 1000 and motiontime <= 3000):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, math.radians(-25)]

            if(motiontime > 3000 and motiontime < 3002):
                # Capture image 
                image = capture_image_at_angle(-60, self.step_counter)
                if image is not None:
                    captured_images.append(image)
                
            if(motiontime > 3002 and motiontime < 3201):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]

            if(motiontime > 3201 and motiontime < 4201):
                self.cmd.mode = 2
                self.cmd.yawSpeed = 0.345433

            if(motiontime > 4201 and motiontime < 4301):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]

            if(motiontime > 4301 and motiontime < 4303):
                # Capture image
                image = capture_image_at_angle(0, self.step_counter)
                if image is not None:
                    captured_images.append(image)

            if(motiontime > 4303 and motiontime < 5303):
                self.cmd.mode = 2
                self.cmd.yawSpeed = 0.305433

            if(motiontime > 5303 and motiontime <= 7300):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, math.radians(25)]

            if(motiontime > 7300 and motiontime < 7302):
                # Capture image
                image = capture_image_at_angle(60, self.step_counter)
                if image is not None:
                    captured_images.append(image)

            if(motiontime > 7302 and motiontime < 7500):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]

            if(motiontime > 7500 and motiontime < 8500):
                self.cmd.mode = 2
                self.cmd.yawSpeed = -0.225433

            if(motiontime > 8500 and motiontime < 8502):
                break  
            self.udp.SetSend(self.cmd)
            self.udp.Send()
            
            

        return captured_images
    
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
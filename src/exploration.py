import time
import cv2
import logging
import networkx as nx
import robot_interface as sdk

from VLM_inference import phi2_query, GPT4V_query, GPT4V_checker, parse_response, GPT4V_baseline
from process_image import process_images, color_code_paths
from robot_utils import capture_images_from_realsense, get_current_position, get_current_yaw_angle
from graph_manager import GraphManager, expand_node_in_directions
from robot_wrapper import Custom, PathPoint



class Exploration:
    def __init__(self, exp_name, type, rrt, n, goal, openai_api_key):
        self.openai_api_key = openai_api_key
        self.n = n
        self.iteration_count = 0
        self.goal = goal
        self.type = type
        self.rrt = rrt
        self.exp_name = exp_name
        self.step_counter = 0
        self.graph = GraphManager()


        # Initialization for robot control
        self.HIGHLEVEL = 0xee
        self.udp = sdk.UDP(self.HIGHLEVEL, 8080, "192.168.123.161", 8082)
        self.cmd = sdk.HighCmd()
        self.state = sdk.HighState()
        self.udp.InitCmdData(self.cmd)

    def explore(self) -> None:
        EXPERIMENT_TYPE = self.type  # Experiment type: RRT, Baseline
        total_CT = 0
        total_TT = 0
        found = False
        images_save_path = 'images'

        while not found:
            print(f"GLOBAL STEP: {self.step_counter}")
            try:
                image1, image2, image3 = capture_images_from_realsense()
            except Exception as e:
                logging.error(f"Error capturing images: {e}")
                break

            processed_image = process_images(image1, image2, image3)

            print("Querying VLM")

            # Descriptions for each image
            desc1 = phi2_query(image1)
            desc2 = phi2_query(image2)
            desc3 = phi2_query(image3)

            desc_list = [desc1, desc2, desc3]

            scores = []  

            if EXPERIMENT_TYPE == "baseline":
                print("Running Baseline")
                start_time = time.time()
                response_base = GPT4V_baseline(path_description, goal=self.goal)
                score_dict = parse_response(response_base)
                for score in score_dict.values():
                    scores.append(score)
                end_time = time.time()
                CT = end_time - start_time
                total_CT += CT
                print(f"ComputationalT: {CT} seconds")

                check = GPT4V_checker(path_description, self.goal, self.openai_api_key)
                print(f"Goal Found? {check}")
                if check.strip().lower() == "yes":
                    print("!!! Found GOAL !!!")
                    found = True
                    break

            elif EXPERIMENT_TYPE == "RRT":
                print("Running RRT")
                for path_description in desc_list:
                    start_time = time.time()
                    self.rrt.run_rrt(path_description)
                    end_time = time.time()
                    CT = end_time - start_time
                    total_CT += CT
                    print(f"ComputationalT: {CT} seconds")
                    print(f"User-Instructions: {self.goal}")

                    check = GPT4V_checker(path_description, self.goal, self.openai_api_key)
                    print(f"Goal Found? {check}")
                    if check.strip().lower() == "yes":
                        print("!!! Found GOAL !!!")
                        found = True
                        break
                    scores.append(score)

            # Visualize path in red
            if scores:
                scored_path_images = color_code_paths(processed_image, scores)
                
                # Save the image
                cv2.imwrite(images_save_path, scored_path_images)

            action_start_time = time.time()

            self.action(self.graph, scores)
            action_end_time = time.time()
            TT = action_end_time - action_start_time
            total_TT += TT
            print(f"TravelT: {TT} seconds")
            print(f"Total TravelT: {total_TT}")
            print(f"Total ComputationalT: {total_CT}")
            self.step_counter += 1

            if found:
                break

    def action(self, graph_manager, scores):
        """Chooses and executes an action based on the scores"""

        # Get current state from SLAM system
        current_position = get_current_position()
        current_yaw = get_current_yaw_angle()

        # Expand nodes in the graph in the given directions with the scores
        graph_manager = expand_node_in_directions(graph_manager, current_position, current_yaw, scores)

        # Find the lowest score node to move to
        target_node_id = graph_manager.find_lowest_score_node()
        target_node_data = graph_manager.graph.nodes[target_node_id]

        # Extract the path point for the robot's control system
        target_path_point = PathPoint(x=target_node_data['position'][0],
                                    y=target_node_data['position'][1],
                                    yaw=target_node_data['yaw'])
        
        path_points = [target_path_point]

        # Call the CPP control method with the path points
        custom.control(path_points)

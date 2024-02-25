import time
import cv2
import logging
import networkx as nx
# import robot_interface as sdk
import numpy as np
import math
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import os

from .VLM_inference import phi2_query, GPT4V_query, GPT4V_checker, success_checker, parse_response, GPT4V_baseline
from .llm_rrt import RRT
from .process_image import process_images, color_code_paths
from .robot_utils import capture_images_from_realsense, get_current_position, get_current_yaw_angle, calculate_new_position_and_yaw
from .graph_manager import GraphManager
# from .speech_utils import SpeechUtils, record_until_silence
# from robot_wrapper import Custom, PathPoint

_simulated_current_position = (0, 0)  # Starting at the origin
_simulated_current_yaw = 0  # Facing "north"

class Exploration:
    def __init__(self, exp_name, type, model, branches, rounds, goal, openai_api_key):
        self.exp_name = exp_name
        self.goal = goal
        self.type = type
        self.openai_api_key = openai_api_key        
        self.rrt = RRT(model, goal, branches, rounds, openai_api_key)
        self.graph_manager = GraphManager()
        # self.speech_utils = SpeechUtils(openai_api_key=openai_api_key)
        self.step_counter = 0
        self.iteration_count = 0

        self.client = OpenAI(api_key=openai_api_key)

        # Initialize the first node
        initial_position = get_current_position()
        initial_yaw = get_current_yaw_angle()
        initial_score = 0
        initial_embedding = None
        self.graph_manager.add_node(initial_position, initial_yaw, initial_score, initial_embedding)


        ## to change back
        # # Initialization for robot control
        # self.HIGHLEVEL = 0xee
        # self.udp = sdk.UDP(self.HIGHLEVEL, 8080, "192.168.123.161", 8082)
        # self.cmd = sdk.HighCmd()
        # self.state = sdk.HighState()
        # self.udp.InitCmdData(self.cmd)

    def get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input = [text], model=model).data[0].embedding

    # def listen_for_goal(self):
    #     print("Listening for the next goal...")
    #     mp3_file = record_until_silence()
    #     goal = self.speech_utils.speech_to_text(mp3_file)
    #     if goal:
    #         print("Heard goal:", goal)
    #     else:
    #         print("Could not understand audio")
    #     return goal

    def announce_goal_found(self):
        response_text = "Goal found, what's next?"
        output_file_path = "path/to/speech_output.mp3"
        self.speech_utils.text_to_speech(response_text, output_file_path)

    def search_or_explore(self):
        # goal = self.listen_for_goal()
        goal = self.goal
        if goal:
            self.goal = goal
            best_node_id = self.search_for_goal()
            if best_node_id is not None:
                self.move_to_node(best_node_id)
                # self.announce_goal_found()
            else:
                print("Exploring for new goals...")
                self.explore()

    def search_for_goal(self):
        highest_similarity = 0
        best_node_id = None
        threshold = 0.8  # Define a threshold for semantic similarity

        for node_id, data in self.graph_manager.graph.nodes(data=True):
            goal_embedding = self.get_embedding(self.goal)
            similarity = cosine_similarity(data['embedding'], goal_embedding)
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_node_id = node_id

        if highest_similarity > threshold:
            print(f"High similarity found: {highest_similarity} at node {best_node_id}")
            return best_node_id
        return None

    def explore(self) -> None:
        EXPERIMENT_TYPE = self.type  # Experiment type: RRT, Baseline
        total_CT = 0
        total_TT = 0
        found = False

        while not found:
            print(f"GLOBAL STEP: {self.step_counter}")
            try:
                # image1, image2, image3 = capture_images_from_realsense()
                image1, image2, image3, path1, path2, path3 = mock_capture_images_from_realsense("src/VLM/images")
            except Exception as e:
                logging.error(f"Error capturing images: {e}")
                break
            image_paths = [path1, path2, path3] 
            processed_image = process_images(image1, image2, image3)

            print("Querying VLM")

            # Descriptions for each image
            desc1 = phi2_query(path1)
            desc2 = phi2_query(path2)
            desc3 = phi2_query(path3)

            desc_list = [desc1, desc2, desc3]
            print(desc_list)
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
                current_position = get_current_position()
                current_yaw = get_current_yaw_angle()
                print(f"=========Current Position: {current_position}, Current Yaw: {current_yaw}")

                directions = [-60, 0, 60]
                fixed_path_length = 1.0
                parent_node_id = self.graph_manager.current_node_id - 1
                for path_description, angle, image_path in zip(desc_list, directions, image_paths):
                    new_position, new_yaw = calculate_new_position_and_yaw(current_position, current_yaw, angle,fixed_path_length)
                    start_time = time.time()
                    score, hullucinations = self.rrt.run_rrt(path_description)
                    end_time = time.time()
                    CT = end_time - start_time
                    total_CT += CT
                    print(f"ComputationalT: {CT} seconds")
                    print(f"User-Instructions: {self.goal}")

                    check = success_checker(image_path, self.goal)
                    print(f"Goal Found? {check}")
                    if check.strip().lower() == "yes":
                        print("!!! Found GOAL !!!")
                        found = True
                        break
                    scores.append(score)

                    # Embed the descriptions
                    desc_embedding = self.get_embedding(path_description)
                    # Creating child nodes
                    
                    new_node_id = self.graph_manager.add_node(new_position, new_yaw, score, desc_embedding)
                    print(f"Child_{new_node_id}_position: {new_position}, Child_{new_node_id}_yaw: {math.degrees(new_yaw)} degrees")
                    
                    self.graph_manager.add_edge(parent_node_id, new_node_id)

                    log_file_path = f"log/node_{new_node_id}_hallucinations.txt"
                    directory = os.path.dirname(log_file_path)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    with open(log_file_path, "w") as file:
                        for hallucination in hullucinations:  
                            file.write(f"{hallucination}\n")

                graph_save_path = f"visualization/graph/step_{self.step_counter}.png"
                directory = os.path.dirname(graph_save_path)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                self.graph_manager.visualize_graph(save_path=graph_save_path)


            # Visualize path in red
                if scores:
                    scored_path_images = color_code_paths(processed_image, scores)

                    ego_images_save_path = 'visualization/egocentric'
                    if not os.path.exists(ego_images_save_path):
                        os.makedirs(ego_images_save_path)
                    output_file_path = os.path.join(ego_images_save_path, f"scored_path_image_{self.step_counter}.png")
                    success = cv2.imwrite(output_file_path, scored_path_images)

                    if not success:
                        print(f"Failed to save the image to {output_file_path}")

            action_start_time = time.time()

            
            best_node_id = self.graph_manager.find_lowest_score_node()

            self.move_to_node(best_node_id)
        

            action_end_time = time.time()
            TT = action_end_time - action_start_time
            total_TT += TT
            print(f"TravelT: {TT} seconds")
            print(f"Total TravelT: {total_TT}")
            print(f"Total ComputationalT: {total_CT}")
            self.step_counter += 1

            if found:
                break

    def move_to_node(self, target_node_id):
        """Chooses and executes an action based on the scores"""

        # target_node_data = self.graph_manager.graph.nodes[target_node_id]

        # # Extract the path point for the robot's control system
        # target_path_point = PathPoint(x=target_node_data['position'][0],
        #                             y=target_node_data['position'][1],
        #                             yaw=target_node_data['yaw'])
        
        # path_points = [target_path_point]

        # # Call the CPP control method with the path points
        # custom.control(path_points)

        target_node_data = self.graph_manager.graph.nodes[target_node_id]
        mock_move_to_node(target_node_data)

def mock_move_to_node(target_node_data):
    global _simulated_current_position, _simulated_current_yaw
    
    # Extract target position and yaw from the node data
    target_position = target_node_data['position']
    target_yaw = target_node_data['yaw']
    
    # Simulate moving by updating the global variables
    _simulated_current_position = target_position
    _simulated_current_yaw = target_yaw
    
    print(f"Mock moving to position: {target_position}, Yaw: {target_yaw} radians")

def mock_capture_images_from_realsense(images_folder="image"):
    left_img_path = os.path.join(images_folder, "left.png")
    mid_img_path = os.path.join(images_folder, "mid.png")
    right_img_path = os.path.join(images_folder, "right.png")

    # Read images using OpenCV
    left_img = cv2.imread(left_img_path)
    mid_img = cv2.imread(mid_img_path)
    right_img = cv2.imread(right_img_path)

    if left_img is None or mid_img is None or right_img is None:
        raise FileNotFoundError("One or more images could not be loaded. Check the paths.")

    return left_img, mid_img, right_img, left_img_path, mid_img_path, right_img_path
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
from .robot_utils import *
from .graph_manager import GraphManager
# from .speech_utils import SpeechUtils, record_until_silence

import sys
sys.path.append('/home/droplab/unitree_sdk2/python_bindings/build')
# print(sys.path) 
import robot_wrapper

_simulated_current_position = (0, 0)  # Starting at the origin
_simulated_current_yaw = 90  # Facing "north"

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
        
        self.serial_numbers = ['936322070007', '238722073643', '242322077802']
        self.pipelines = initialize_cameras(self.serial_numbers)
        print("111")
        robot_wrapper.Custom.initialize()
        self.custom = robot_wrapper.Custom()
        self.custom.dt = 0.002
        print("222")
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
        best_node_id = 0
        average_depths = []
        image_paths = []
        # path_to_lowest_score_node = [0]
        while not found:
            print(f"GLOBAL STEP: {self.step_counter}")
            
            for i, pipeline in enumerate(self.pipelines):
                image, avg_depth, path = capture_image_and_average_depth(pipeline, self.serial_numbers[i])
                if path:
                    image_paths.append(path)
                    average_depths.append(avg_depth)
            if len(image_paths) == len(self.pipelines):  # Ensure all images were captured
                processed_images = process_images(*[cv2.imread(p) for p in image_paths])
            
            print("Querying VLM")
            print("image_paths", image_paths)
            descriptions = [phi2_query(path) for path in image_paths]
            print("description_list:", descriptions)
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
                # current_position = get_current_position()
                # current_yaw = get_current_yaw_angle()
                # Mock 
                current_position = self.graph_manager.graph.nodes[best_node_id]["position"]
                current_yaw = self.graph_manager.graph.nodes[best_node_id]["yaw"]
                print(f"Current Position: {current_position}, Current Yaw: {current_yaw}")

                directions = [-60, 0, 60]
                fixed_offset = 1.0
                parent_node_id = best_node_id
                print(f"****parent_node_id{parent_node_id}")
                for path_description, angle, image_path in zip(descriptions, directions, image_paths):

                    dynamic_path_length = calculate_path_length_based_on_depth(avg_depth)

                    new_position, new_yaw = calculate_new_position_and_yaw(
                        current_position, current_yaw, angle, dynamic_path_length)
                    start_time = time.time()
                    score, hallucinations = self.rrt.run_rrt(path_description)
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
                    print(f"node_{new_node_id}_position: {new_position}, yaw: {math.degrees(new_yaw)} degrees")
                    
                    self.graph_manager.add_edge(parent_node_id, new_node_id)

                    log_file_path = f"log/node_{new_node_id}_hallucinations.txt"
                    directory = os.path.dirname(log_file_path)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    with open(log_file_path, "w") as file:
                        for hallucination in hallucinations:  
                            file.write(f"{hallucination}\n")

            # Visualize path in red
                if scores:
                    scored_path_images = color_code_paths(processed_images, scores)

                    ego_images_save_path = 'visualization/egocentric'
                    if not os.path.exists(ego_images_save_path):
                        os.makedirs(ego_images_save_path)
                    output_file_path = os.path.join(ego_images_save_path, f"scored_path_image_{self.step_counter}.png")
                    success = cv2.imwrite(output_file_path, scored_path_images)

                    if not success:
                        print(f"Failed to save the image to {output_file_path}")

            action_start_time = time.time()

            # best_node_id +=1
            best_node_id = self.graph_manager.find_highest_score_unvisited_node()

            path_to_lowest_score_node = self.graph_manager.find_shortest_path_to_highest_score_node(parent_node_id)
            graph_save_path = f"visualization/graph/step_{self.step_counter}.png"
            directory = os.path.dirname(graph_save_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.graph_manager.visualize_graph(path=path_to_lowest_score_node, show_labels=True, save_path=graph_save_path)

            print(f"Path_to_lowest_score{path_to_lowest_score_node}")
            self.move_to_node(best_node_id)
            self.graph_manager.mark_node_as_visited(best_node_id)

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
        target_node_data = self.graph_manager.graph.nodes[target_node_id]
        self.custom.moveToPositionAndYaw(target_node_data['position'][0], 
                                        target_node_data['position'][1], 
                                        target_node_data['yaw'])

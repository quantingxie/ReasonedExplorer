import time
import cv2
import logging
from VLM_inference import phi2_query, GPT4V_query, GPT4V_checker, parse_response, GPT4V_baseline
from process_image import process_images, color_code_paths
import robot_interface as sdk
from robot_utils import capture_images_from_realsense


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
                image1, image2 = capture_images_from_realsense()
            except Exception as e:
                logging.error(f"Error capturing images: {e}")
                break

            processed_image = process_images(image1, image2)

            print("Querying VLM")
            response = GPT4V_query(processed_image, self.openai_api_key)

            path_dict = parse_response(response)
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
                for path_description in path_dict.values():
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
            self.action()
            action_end_time = time.time()
            TT = action_end_time - action_start_time
            total_TT += TT
            print(f"TravelT: {TT} seconds")
            print(f"Total TravelT: {total_TT}")
            print(f"Total ComputationalT: {total_CT}")
            self.step_counter += 1

            if found:
                break

    def action(self) -> None:
        """Chooses and executes an action based on the Q-values."""
        # Implementation of robot action logic goes here

        # TODO: Need to read GO2
import math
import time
import networkx as nx
import cv2
from typing import List, Tuple
from LLM_functions import LLM_abstractor, LLM_rephraser, LLM_checker
from VLM import VLM_query
from utils import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import logging
import keyboard
from LLM_functions import LLM_evaluator
import robot_interface as sdk

MY_API_KEY = "AIzaSyC9vS1own2-T3scUJPZdefXLYBnUQr1pSE"

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
    def __init__(self):
        self.frontier_buffer = []
        self.step_counter = 0
        self.Q_buffer = {}  # Dictionary to store Q-values for nodes
        logging.basicConfig(filename='exploration.log', level=logging.INFO, format='%(message)s')
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


    def explore(self) -> None:
        # Initialize current_node at the beginning of exploration

        total_CT = 0
        total_TT = 0
        while True:

            captured_images = self.capture_images_by_rotate(self.n, self.rom)

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
        print("Press 'enter' to start the action and 'enter again' to end the action.")
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
            if(motiontime > 1000 and motiontime < 2000):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, math.radians(-25)]
            if(motiontime > 2000 and motiontime < 2002):
                # Capture image 
                image = capture_image_at_angle(-60, self.step_counter)
                if image is not None:
                    captured_images.append(image)
                
            if(motiontime > 2002 and motiontime < 2201):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]
            if(motiontime > 2201 and motiontime < 3201):
                self.cmd.mode = 2
                self.cmd.yawSpeed = 0.345433
            if(motiontime > 3201 and motiontime < 3301):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]
            if(motiontime > 3301 and motiontime < 3303):
                # Capture image
                image = capture_image_at_angle(0, self.step_counter)
                if image is not None:
                    captured_images.append(image)
            if(motiontime > 3303 and motiontime < 4303):
                self.cmd.mode = 2
                self.cmd.yawSpeed = 0.305433
            if(motiontime > 4303 and motiontime < 5300):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, math.radians(25)]
            if(motiontime > 5300 and motiontime < 5302):
                # Capture image
                image = capture_image_at_angle(0, self.step_counter)
                if image is not None:
                    captured_images.append(image)
            if(motiontime > 5302 and motiontime < 5500):
                self.cmd.mode = 1
                self.cmd.euler = [0, 0, 0]

            if(motiontime > 5500 and motiontime < 6500):
                self.cmd.mode = 2
                self.cmd.yawSpeed = -0.225433

            if(motiontime > 6500 and motiontime < 6502):
                break  
            self.udp.SetSend(self.cmd)
            self.udp.Send()
            
            
        return captured_images
    
explore_instance = Exploration()
explore_instance.explore()
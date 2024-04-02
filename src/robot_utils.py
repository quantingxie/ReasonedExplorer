import numpy as np
import threading
import socket
import time
import sys
import math
import serial
# import robot_interface as sdk
sys.path.append('../lib/python/arm64')
import pyrealsense2 as rs
import random
import cv2
import os
# Initialize global variables to keep track of the simulated robot's state
_simulated_x, _simulated_y, _simulated_yaw = 0.0, 0.0, 0.0

def get_current_position():
    global _simulated_x, _simulated_y
    # Simulate movement by adding a small random value to the position
    _simulated_x += random.uniform(-0.5, 0.5)  # Simulate movement in X direction
    _simulated_y += random.uniform(-0.5, 0.5)  # Simulate movement in Y direction
    return (_simulated_x, _simulated_y)

def get_current_yaw_angle():
    global _simulated_yaw
    # Simulate rotation by adding a small random value to the yaw angle
    _simulated_yaw += random.uniform(-math.radians(10), math.radians(10))  # Simulate rotation
    _simulated_yaw = _simulated_yaw % (2 * math.pi)  # Ensure yaw stays within a 0 to 2π range
    return _simulated_yaw


def initialize_cameras(serial_numbers, delay=5):
    pipelines = []
    for serial_number in serial_numbers:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_device(serial_number)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 6)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 6)
        pipeline.start(config)
        pipelines.append(pipeline)
        
    print("Cameras initialized. Waiting for auto-exposure adjustment for 5s...")
    time.sleep(delay)
    return pipelines

def capture_image_from_camera(pipeline):
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        return None
    color_image = np.asanyarray(color_frame.get_data())
    return color_image

def capture_image_and_average_depth(pipeline, serial_number, image_folder="log_images"):
    try:
        os.makedirs(image_folder, exist_ok=True)  # Ensure the directory exists
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            return None, None, None

        # Process depth frame
        depth_image = np.asanyarray(depth_frame.get_data())
        non_zero_depths = depth_image[depth_image != 0]
        average_depth = np.mean(non_zero_depths) if non_zero_depths.size > 0 else 0

        # Process color frame and save image
        color_image = np.asanyarray(color_frame.get_data())
        filename = f"camera_{serial_number}.jpg"
        filepath = os.path.join(image_folder, filename)
        print("filepath", filepath)

        cv2.imwrite(filepath, color_image)

        return color_image, average_depth, filepath
    except Exception as e:
        print(f"Failed to capture images: {e}")
        return None, None, None


# def get_current_position():
#     # Mock implementation. Replace with actual SLAM system integration.
#     return (0, 0)  # Return the current (x, y) position of the robot.

# def get_current_yaw_angle():
#     # Mock implementation. Replace with actual SLAM system integration.
#     return 0  # Return the current yaw angle of the robot in radians.

def socket_client_thread():
    global current_lat, current_lon
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect(('127.0.0.1', 12345))

    while True:
        # Receive data from the server
        received_data = s.recv(1024).decode('utf-8')

        # Convert received data to tuple and extract lat and lon
        lat, lon = eval(received_data)
        current_lat, current_lon = lat, lon

def get_GPS():
    """Fetch the latest GPS coordinates."""
    global current_lat, current_lon
    return current_lat, current_lon


def calculate_distance(pos1, pos2):
    dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
    return dist



def calculate_new_position_and_yaw(current_position, current_yaw, angle, path_length):
    print(f"========angle{angle}, current pos{current_position}, current yaw {current_yaw}")
    angle_rad = math.radians(angle)
    new_x = current_position[0] + path_length * math.cos(current_yaw + angle_rad)
    new_y = current_position[1] + path_length * math.sin(current_yaw + angle_rad)
    new_yaw = (current_yaw + angle_rad) % (2 * math.pi)
    return (new_x, new_y), new_yaw


def calculate_path_length_based_on_depth(avg_depth):
    max_depth_threshold = 3.0  # Example threshold
    min_path_length = 0.5
    max_path_length = 2.0

    if avg_depth > max_depth_threshold:
        return max_path_length
    else:
        return min_path_length + (avg_depth / max_depth_threshold) * (max_path_length - min_path_length)
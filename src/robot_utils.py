import numpy as np
import threading
import socket
import time
import sys
import math
import serial
# import robot_interface as sdk
sys.path.append('../lib/python/arm64')
# import pyrealsense2 as rs
import numpy as np
import random
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

def capture_images_from_realsense():
    # Configure the first camera
    pipeline_1 = rs.pipeline()
    config_1 = rs.config()
    config_1.enable_device('serial_number_1')  # Replace with the actual serial number of your first camera
    config_1.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Configure the second camera
    pipeline_2 = rs.pipeline()
    config_2 = rs.config()
    config_2.enable_device('serial_number_2')  # Replace with the actual serial number of your second camera
    config_2.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Configure the second camera
    pipeline_3 = rs.pipeline()
    config_3 = rs.config()
    config_3.enable_device('serial_number_3')  # Replace with the actual serial number of your second camera
    config_3.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start the configured pipelines to begin streaming
    pipeline_1.start(config_1)
    pipeline_2.start(config_2)
    pipeline_3.start(config_3)

    try:
        # Wait for a coherent pair of frames: depth and color
        frames_1 = pipeline_1.wait_for_frames()
        frames_2 = pipeline_2.wait_for_frames()
        frames_3 = pipeline_3.wait_for_frames()

        # Get color frames
        color_frame_1 = frames_1.get_color_frame()
        color_frame_2 = frames_2.get_color_frame()
        color_frame_3 = frames_3.get_color_frame()

        # Convert images to numpy arrays
        image_1 = np.asanyarray(color_frame_1.get_data())
        image_2 = np.asanyarray(color_frame_2.get_data())
        image_3 = np.asanyarray(color_frame_3.get_data())

        return image_1, image_2, image_3

    finally:
        # Stop streaming
        pipeline_1.stop()
        pipeline_2.stop()
        pipeline_3.stop()

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
    angle_rad = math.radians(angle)
    new_x = current_position[0] + path_length * math.cos(current_yaw + angle_rad)
    new_y = current_position[1] + path_length * math.sin(current_yaw + angle_rad)
    new_yaw = (current_yaw + angle_rad) % (2 * math.pi)
    return (new_x, new_y), new_yaw

import cv2
import numpy as np
import threading
import socket
import time
import sys
import math
import robot_interface as sdk
from pyproj import Proj, Transformer, CRS
sys.path.append('../lib/python/arm64')


def capture_image_at_angle(angle):
    camera = cv2.VideoCapture(1)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return
    
    ret, frame = camera.read()
    frame = cv2.flip(frame, 0)
    frame = cv2.flip(frame, 1)

    cv2.imwrite(f"{angle}_degrees.jpg", frame)

    if not ret:
        print(f"Error: Couldn't capture image at angle {angle}.")
        return None

    return f"{angle}_degrees.jpg"

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


# def capture_images_by_rotate(n: int, range_of_motion=70) -> list:
#     HIGHLEVEL = 0xee
#     udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
#     cmd = sdk.HighCmd()
#     udp.InitCmdData(cmd)

#     captured_images = []

#     # Calculate min_angle and max_angle based on range_of_motion
#     min_angle = -range_of_motion / 2
#     max_angle = range_of_motion / 2

#     # Calculate the angle increment
#     angle_increment = math.radians(range_of_motion) / n

#     # Capture images while rotating to the left (from 0 to min_angle)
#     for i in range(0, n//2):  # Half of the images in this direction
#         yaw_angle = min_angle + i * angle_increment

#         cmd.euler = [0, 0, yaw_angle]
#         cmd.mode = 1

#         udp.SetSend(cmd)
#         udp.Send()
#         time.sleep(1)

#         angle_in_degrees = math.degrees(yaw_angle)
#         image = capture_image_at_angle(angle_in_degrees)
#         if image is not None:
#             captured_images.append(image)

#     # Reset to 0 before moving to the right
#     cmd.euler = [0, 0, 0]
#     udp.SetSend(cmd)
#     udp.Send()
#     time.sleep(1)

#     # Capture images while rotating to the right (from 0 to max_angle)
#     for i in range(n//2, n):  # The other half of the images in this direction
#         yaw_angle = i * angle_increment

#         cmd.euler = [0, 0, yaw_angle]
#         cmd.mode = 1

#         udp.SetSend(cmd)
#         udp.Send()
#         time.sleep(1)

#         angle_in_degrees = math.degrees(yaw_angle)
#         image = capture_image_at_angle(angle_in_degrees)
#         if image is not None:
#             captured_images.append(image)

#     # Reset the robot's position after capturing all images
#     cmd.euler = [0, 0, 0]
#     udp.SetSend(cmd)
#     udp.Send()

#     return captured_images

# def move_to_next_point(next_position):
#     # Initialize PID variables
#     integral = 0
#     previous_error = 0
#     yaw_integral = 0
#     previous_yaw_error = 0

#     # Connection setup
#     HIGHLEVEL = 0xee
#     udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
#     cmd = sdk.HighCmd()
#     state = sdk.HighState()
#     udp.InitCmdData(cmd)

#     # Using the next_position as the waypoint directly
#     try:
#         while True:
#             udp.Recv()
#             udp.GetRecv(state)

#             dt = 0.01
#             current_pos = get_GPS()
#             current_yaw = state.imu.rpy[2]  # Get the current yaw from the state data

#             cmd.mode = 2
#             cmd.gaitType = 1
#             cmd.bodyHeight = 0.1

#             v, y, previous_error, previous_yaw_error, _, _ = calculate_velocity_yaw(current_pos, next_position, current_yaw, dt, integral, previous_error, yaw_integral, previous_yaw_error)
#             v = np.clip(v, -0.2, 0.2)
#             cmd.velocity = [v, 0]
#             cmd.yawSpeed = y

#             udp.SetSend(cmd)
#             udp.Send()

#             # Break condition: If the robot is close to next_position
#             if calculate_distance(current_pos, next_position) < 0.1:
#                 break

#     except Exception as e:
#         print(f"Error occurred in the control loop: {e}")
    
def calculate_velocity_yaw(current_pos, waypoint, current_yaw, dt, integral, previous_error, yaw_integral, previous_yaw_error):
    # Initialize PID gains
    Kp = 0.8
    Ki = 0.2
    Kd = 0.02

    Kp_yaw = 0.8
    Ki_yaw = 0.2
    Kd_yaw = 0.02
    EPSILON = 1e-6

    # For the distance PID control
    error = calculate_distance(current_pos, waypoint)
    # print("error", error)
    integral += error * dt
    derivative = (error - previous_error) / (dt + EPSILON)
    velocity = Kp * error + Ki * integral + Kd * derivative
    # print("velocity", velocity)
    # For the yaw PID control
    desired_yaw = math.atan2(waypoint[1] - current_pos[1], waypoint[0] - current_pos[0])
    yaw_error = desired_yaw - current_yaw
    # Ensure yaw_error is between -pi and pi
    yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
    yaw_integral += yaw_error * dt
    yaw_derivative = (yaw_error - previous_yaw_error) / (dt + EPSILON)

    yaw_speed = Kp_yaw * yaw_error + Ki_yaw * yaw_integral + Kd_yaw * yaw_derivative
    return velocity, yaw_speed, error, yaw_error, waypoint, desired_yaw

def calculate_distance(pos1, pos2):
    dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
    return dist
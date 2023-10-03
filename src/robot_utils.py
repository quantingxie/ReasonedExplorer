import cv2
import numpy as np
import threading
import socket
import time
import sys
import math
import serial
import robot_interface as sdk
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

def adjust_heading(heading):
    if 0 <= heading <= 180:
        return -heading
    elif 180 < heading <= 360:
        return -(heading - 360)

def get_yaw(port='/dev/ttyUSB0', baudrate=9600, timeout=1):
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            line = ser.readline()  # read a line terminated with a newline (\n)
            try:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('$PRDID'):
                    # Split the line by commas
                    parts = decoded_line.split(',')
                    # Heading (relative to true north) is the third value in the list
                    heading = float(parts[2])  # changed from parts[3] to parts[2] as lists are 0-indexed
                    adjusted_heading = adjust_heading(heading)
                    yield adjusted_heading
            except UnicodeDecodeError:
                # Silently ignore decoding errors
                pass
            except Exception as e:
                print(f"Unexpected error: {e}")


def calculate_velocity_yaw(current_pos, current_yaw, waypoint, desired_node_yaw):
    Kp_yaw = 0.4
    Ki_yaw = 0.2
    Kd_yaw = 0.02
    EPSILON = 1e-6
    position_error = haversine_distance(current_pos, waypoint)
    dlat = waypoint[0] - current_pos[0]
    dlon = waypoint[1] - current_pos[1]

    if position_error > 1:  # If the robot is further than 1 unit from the waypoint
        desired_yaw = math.atan2(dlat, dlon)
        desired_yaw = desired_yaw - np.pi/2 
    else:
        desired_yaw = desired_node_yaw  # Set desired yaw to the node's yaw as the robot gets closer

    desired_yaw = (desired_yaw + np.pi) % (2 * np.pi) - np.pi

    yaw_error = desired_yaw - current_yaw
    yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
    
    yaw_integral = 0  # Initialize this in your global scope if you want integral action
    previous_yaw_error = 0  # Initialize this in your global scope

    dt = 0.01  # Consider adjusting this as per your needs
    yaw_integral += yaw_error * dt
    yaw_derivative = (yaw_error - previous_yaw_error) / (dt + EPSILON)
    yaw_speed = Kp_yaw * yaw_error + Ki_yaw * yaw_integral + Kd_yaw * yaw_derivative
    return 0.2, yaw_speed, yaw_error, position_error, desired_yaw


def calculate_distance(pos1, pos2):
    dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
    return dist

def haversine_distance(current, waypoint):
    lat1, lon1 = current
    lat2, lon2 = waypoint
    
    R = 6371e3  # Earth radius in meters
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c



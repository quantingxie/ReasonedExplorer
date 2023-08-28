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


def capture_images_by_rotate(n: int, range_of_motion=70) -> list:
    HIGHLEVEL = 0xee
    udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
    cmd = sdk.HighCmd()
    udp.InitCmdData(cmd)

    captured_images = []

    # Calculate min_angle and max_angle based on range_of_motion
    min_angle = -range_of_motion / 2
    max_angle = range_of_motion / 2

    # Calculate the angle increment
    angle_increment = math.radians(range_of_motion) / n

    # Capture images while rotating to the left (from 0 to min_angle)
    for i in range(0, n//2):  # Half of the images in this direction
        yaw_angle = min_angle + i * angle_increment

        cmd.euler = [0, 0, yaw_angle]
        cmd.mode = 1

        udp.SetSend(cmd)
        udp.Send()
        time.sleep(1)

        angle_in_degrees = math.degrees(yaw_angle)
        image = capture_image_at_angle(angle_in_degrees)
        if image is not None:
            captured_images.append(image)

    # Reset to 0 before moving to the right
    cmd.euler = [0, 0, 0]
    udp.SetSend(cmd)
    udp.Send()
    time.sleep(1)

    # Capture images while rotating to the right (from 0 to max_angle)
    for i in range(n//2, n):  # The other half of the images in this direction
        yaw_angle = i * angle_increment

        cmd.euler = [0, 0, yaw_angle]
        cmd.mode = 1

        udp.SetSend(cmd)
        udp.Send()
        time.sleep(1)

        angle_in_degrees = math.degrees(yaw_angle)
        image = capture_image_at_angle(angle_in_degrees)
        if image is not None:
            captured_images.append(image)

    # Reset the robot's position after capturing all images
    cmd.euler = [0, 0, 0]
    udp.SetSend(cmd)
    udp.Send()

    return captured_images

def move_to_next_point(current_position, next_position):
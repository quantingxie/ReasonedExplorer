import sys
import time
import math
import numpy as np
import threading
import socket
import serial
sys.path.append('../lib/python/arm64')
import robot_interface as sdk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pyproj import Proj, Transformer, CRS

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='robot_yaw.log',   # This will log to a file named "robot_yaw.log"
                    filemode='w')   
# Initialize global variables for latitude and longitude
current_lat = None
current_lon = None


def dms_to_dd(dms):
    if dms < 0:
        dms = abs(dms)
        degrees = math.floor(abs(dms))
        fractional = abs(dms) - abs(degrees)
        minutes = fractional * 100 / 60
        return -(degrees + minutes)
    else:
        degrees = math.floor(dms)
        fractional = dms - degrees
        minutes = fractional * 100 / 60
        return degrees + minutes




# def socket_client_thread():
#     global initial_lat, initial_lon, current_lat, current_lon
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     # Connect to the server
#     s.connect(('127.0.0.1', 12345))
#     with open('gps_data_log.txt' , 'w') as f:

#         while True:
#             # Receive data from the server
#             received_data = s.recv(1024).decode('utf-8')
#             # print(f"Received data: {received_data}")
#             f.write(received_data + '\n')
#             # Convert received data to tuple and extract lat and lon
#             lat, lon = eval(received_data)
        
#             current_lat, current_lon = lat, -lon
        
#             if initial_lat is None and initial_lon is None:
#                 initial_lat, initial_lon = lat, lon

def adjust_heading(heading):
    if 0 <= heading <= 180:
        return -heading
    elif 180 < heading <= 360:
        return -(heading - 360)

def get_GPS(port='/dev/ttyUSB1', baudrate=38400, timeout=1):
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            while True:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line.startswith('$GNGLL'):
                    split_line = line.split(',')
                    lat = dms_to_dd(float(split_line[1])/100)  # make sure dms_to_dd is defined
                    lon = dms_to_dd(float(split_line[3])/100)
                    # print(lat, -lon)
                    return lat, -lon
    except Exception as e:
        print(f"An error occurred in get_GPS: {e}")


def get_yaw(port='/dev/ttyUSB0', baudrate=115200, timeout=0.1):
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            line = ser. readline()  # read a line terminated with a newline (\n)
            try:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('$HCHDG'):
                    # Split the line by commas
                    parts = decoded_line.split(',')
                    # Heading (relative to true north) is the third value in the list
                    heading = float(parts[1])  # changed from parts[3] to parts[2] as lists are 0-indexed
                    adjusted_heading = adjust_heading(heading)
                    # print("adjusted heading", adjusted_heading)
                    return adjusted_heading
            except UnicodeDecodeError:
                # Silently ignore decoding errors
                pass
            except Exception as e:
                print(f"Unexpected error: {e}")



# Define function for distance calculation
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

class RobotController:
    def __init__(self):
        self.ser_GPS = serial.Serial('/dev/ttyUSB1', 38400, timeout=1)
        self.ser_yaw = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)

    def get_GPS(self):
        while True:
            line = self.ser_GPS.readline().decode('utf-8', errors='replace').strip()
            if line.startswith('$GNGLL'):
                split_line = line.split(',')
                lat = dms_to_dd(float(split_line[1])/100)
                lon = dms_to_dd(float(split_line[3])/100)
                return lat, -lon

    def get_yaw(self):
        while True:
            line = self.ser_yaw.readline()
            try:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('$HCHDG'):
                    parts = decoded_line.split(',')
                    heading = float(parts[1])
                    adjusted_heading = adjust_heading(heading)
                    return adjusted_heading
            except UnicodeDecodeError:
                pass

    def close_connections(self):
        self.ser_GPS.close()
        self.ser_yaw.close()


EPSILON = 1e-6  # A small value
print("222")
# raw_yaw_generator = get_yaw() # Initialize the generator
# print("testing")
# raw_gps_generator = get_GPS()
# current_yaw = next(raw_yaw_generator) # Fetch the latest yaw from the generator
# current_lat, current_lon = next(raw_gps_generator)# logging.debug(f"Current Yaw from generator: {current_yaw}")
print("333")
# yaw_offset = math.radians(-96) 
next_point = np.array([40.443656, -79.944091])
curret_pos = ([40.443681, 79.944285])
def calculate_yaw_control(current_pos, current_yaw, waypoint):
    position_error = haversine_distance(current_pos, waypoint)
    dlat = waypoint[0] - current_pos[0]
    dlon = waypoint[1] - current_pos[1]
    # print("Current yaw in control", current_yaw)
    desired_yaw = math.atan2(dlat, dlon)
    desired_yaw = desired_yaw - np.pi/2 
    desired_yaw = (desired_yaw + np.pi) % (2 * np.pi) - np.pi
    # print("Desired yaw in control", desired_yaw)

    yaw_error = desired_yaw - math.radians(current_yaw)
    yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
    # yaw_error = math.radians(yaw_error)
    Kp_yaw = 0.05
    Ki_yaw = 0.2
    Kd_yaw = 0.02
    Kp_yaw = 0.5
    Ki_yaw = 0.2
    Kd_yaw = 0.02
    yaw_integral = 0  # Initialize this in your global scope if you want integral action
    previous_yaw_error = 0  # Initialize this in your global scope

    dt = 0.01  # Consider adjusting this as per your needs
    yaw_integral += yaw_error * dt
    yaw_derivative = (yaw_error - previous_yaw_error) / (dt + EPSILON)
    yaw_speed = Kp_yaw * yaw_error + Ki_yaw * yaw_integral + Kd_yaw * yaw_derivative
    return 0.2, yaw_speed, yaw_error, position_error, desired_yaw

if __name__ == '__main__':

    # Start socket client in a separate thread
    # threading.Thread(target=socket_client_thread).start()
    print("111")
    HIGHLEVEL = 0xee
    LOWLEVEL = 0xff

    udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
    print("UDP Initialized")
    cmd = sdk.HighCmd()
    state = sdk.HighState()
    udp.InitCmdData(cmd)

    # Initialize PID variables
    integral = 0
    previous_error = 0
    yaw_integral = 0
    previous_yaw_error = 0

    print_frequency = 0.05  # Print every 0.05 seconds
    last_print_time = time.time()  # Initialize the last print time

    path_x, path_y = [], []
    current_x, current_y = [], []
    errors, yaw_errors, times = [], [], []
    controller = RobotController()
    try:
        waypoint = next_point
        while True:
            udp.Recv()
            udp.GetRecv(state)

            current_lat, current_lon = controller.get_GPS()
            print(current_lat, current_lon)
            current_pos = np.array([current_lat, current_lon])

            current_yaw = controller.get_yaw()
            print("TEsting yaw", current_yaw)
            cmd.mode = 2
            cmd.gaitType = 1
            cmd.bodyHeight = 0.1

            v, y, yaw_error, position_error, desired_yaw = calculate_yaw_control(current_pos, current_yaw, waypoint)
            cmd.velocity = [0, 0]
            cmd.yawSpeed = 0
            if time.time() - last_print_time >= print_frequency:
                print(f"Desired Yaw (to waypoint): {math.degrees(desired_yaw)} degrees")
                print(f"Current Yaw after getting from generator: {current_yaw}")
                print(f"Current Position: {current_pos}")
                print(f"Sending command velocity: {v}, yaw speed: {y}")
                print(f"Position Error: {position_error}, Yaw Error: {yaw_error}\n")
                last_print_time = time.time()  # Update the last print time

            current_x.append(current_pos[0])
            current_y.append(current_pos[1])
            path_x.append(waypoint[0])
            path_y.append(waypoint[1])
            errors.append(position_error)
            yaw_errors.append(yaw_error)
            times.append(time.time())

            udp.SetSend(cmd)
            udp.Send()

            if haversine_distance(current_pos, waypoint) < 1.0:  # If the robot is close enough to the waypoint, break the loop
                break

    except Exception as e:
        print(f"Error occurred in the control loop: {e}")
        # Depending on the error, you might want to break out of the control loop
    except KeyboardInterrupt:
        print("Interrupted by user, stopping the robot...")
    finally:
        # Create a new figure for the plots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

        # Plot the path
        ax1.plot(path_x, path_y, label='Desired Path')
        ax1.plot(current_x, current_y, label='Robot Path')
        ax1.set_xlabel('X position')
        ax1.set_ylabel('Y position')
        ax1.legend()

        # Plot the position error over time
        ax2.plot(times, errors, label='Position Error')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Position Error')
        ax2.legend()

        # Plot the yaw error over time
        ax3.plot(times, yaw_errors, label='Yaw Error')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Yaw Error')
        ax3.legend()

        # Show the plots
        plt.show()

        # Stop the robot
        cmd.mode = 0
        cmd.velocity = [0, 0]
        cmd.yawSpeed = 0
        udp.SetSend(cmd)
        udp.Send()

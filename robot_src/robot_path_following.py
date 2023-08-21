import sys
import time
import math
import numpy as np
import threading
import socket

sys.path.append('../lib/python/arm64')
import robot_interface as sdk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pyproj import Proj, Transformer, CRS


# Initialize global variables for latitude and longitude
initial_lat = None
initial_lon = None
current_lat = None
current_lon = None

# Set desired path as a list of (x, y) waypoints
relative_path = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 0.0]])


# Set PID gains for the controller
Kp = 0.8
Ki = 0.2
Kd = 0.02

Kp_yaw = 0.8
Ki_yaw = 0.2
Kd_yaw = 0.02

def socket_client_thread():
    global initial_lat, initial_lon, current_lat, current_lon
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect(('127.0.0.1', 12345))
    with open('gps_data_log.txt' , 'w') as f:

        while True:
            # Receive data from the server
            received_data = s.recv(1024).decode('utf-8')
            # print(f"Received data: {received_data}")
            f.write(received_data + '\n')
            # Convert received data to tuple and extract lat and lon
            lat, lon = eval(received_data)
        
            current_lat, current_lon = lat, lon
        
            if initial_lat is None and initial_lon is None:
                initial_lat, initial_lon = lat, lon
def convert_relative_to_gps(init_lat, init_lon, dx, dy):
    # Define the coordinate systems
    wgs84 = CRS('EPSG:4326')  # WGS84 geographic CRS (lat/lon)
    utm = CRS('EPSG:32632')  # Or whatever UTM zone is relevant

    if init_lat is None or init_lon is None:
        print("latitude or longitude is None!")
        return None, None

    # Convert initial point to UTM
    transformer_to_utm = Transformer.from_crs(wgs84, utm)
    #print(f"Initial latitude: {init_lat}, type: {type(init_lat)}")
    #print(f"Initial longitude: {init_lon}, type: {type(init_lon)}")
    x, y = transformer_to_utm.transform(init_lat, init_lon)

    # Add the relative distances
    #print(f"x {x}, y {y}")
    x += dx
    y += dy
    
    #print(f"goal x {x}, goal y {y}, dx {dx}, dy {dy}")
    transformer_to_wgs84 = Transformer.from_crs(utm, wgs84)
    # Convert the new point back to lat and lon
    lat, lon = transformer_to_wgs84.transform(x, y)
    
    #print(f"Goal latitude and longitude: ({lat}, {lon})")  # New print statement
    
    return x, y

# Define function for distance calculation
def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

EPSILON = 1e-6  # A small value

def calculate_velocity_yaw(current_pos, waypoint, current_yaw, dt, integral, previous_error, yaw_integral, previous_yaw_error):
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





if __name__ == '__main__':

    # Start socket client in a separate thread
    threading.Thread(target=socket_client_thread).start()

    HIGHLEVEL = 0xee
    LOWLEVEL  = 0xff

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
    try:
        for relative_point in relative_path:
            print(f"relative point x {relative_point[0]}, relative point y {relative_point[1]}")
            waypoint = convert_relative_to_gps(initial_lat, initial_lon, relative_point[0], relative_point[1])            
            
            while True:
                try:
                    udp.Recv()
                    udp.GetRecv(state)

                    dt = 0.01            
                    # Update position from state data or GPS data
                    if current_lat is not None and current_lon is not None:
                        #current_pos = np.array([current_lat, current_lon])
                         current_pos = convert_relative_to_gps(current_lat, current_lon, 0,0)
                    else:
                        print("No GPS data yet")
                        time.sleep(0.1)  # Give some time for GPS data to arrive
                        continue

                    current_yaw = state.imu.rpy[2]  # Get the current yaw from the state data
                    
                    cmd.mode = 2
                    cmd.gaitType = 1
                    cmd.bodyHeight = 0.1

                    v, y, previous_error, previous_yaw_error, waypoint, desired_yaw = calculate_velocity_yaw(current_pos, waypoint, current_yaw, dt, integral, previous_error, yaw_integral, previous_yaw_error)
                    # print(v)
                    v = np.clip(v, -0.2, 0.2)
                    cmd.velocity = [v,0]
                    cmd.yawSpeed = y
                    if time.time() - last_print_time >= print_frequency:
                        #print(f"Command Velocity: {cmd.velocity}")
                        print(f"Current Position: {current_pos}")
                        print(f"Current yaw: {current_yaw}")
                        print(f"Sending command velocity: {v}, yaw speed: {y}")
                        print(f"Goal: {waypoint}, desired_yaw: {desired_yaw}")
                        print(f"Position Error: {previous_error}, Yaw Error: {previous_yaw_error}\n")
                        #print(f"PID error: {previous_error}, integral: {integral}, derivative: {derivative}\n")

                        last_print_time = time.time()  # Update the last print time

                    current_x.append(current_pos[0])
                    current_y.append(current_pos[1])
                    path_x.append(waypoint[0])
                    path_y.append(waypoint[1])
                    errors.append(previous_error)
                    yaw_errors.append(previous_yaw_error)
                    times.append(time.time())

                    udp.SetSend(cmd)
                    udp.Send()
                except Exception as e:
                    print(f"Error occurred in the control loop: {e}")
                    # Depending on the error, you might want to break out of the control loop
                    break
                
                if calculate_distance(current_pos, waypoint) < 0.1:  # If the robot is close enough to the waypoint, break the loop
                    break
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
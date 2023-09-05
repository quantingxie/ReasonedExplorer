# import airsim
# import math
# import numpy as np
# import time
# import matplotlib.pyplot as plt
# kp_yaw = 3
# ki_yaw = 0.01
# kd_yaw = 0.02
# desired_position = [10, 20]

# previous_error = 0
# integral = 0
# def set_yaw_to_zero(client):
#     pose = client.simGetVehiclePose()
#     pitch, roll, _ = airsim.to_eularian_angles(pose.orientation)
#     new_orientation = airsim.to_quaternion(pitch, roll, math.radians(-30))
#     pose.orientation = new_orientation
#     client.simSetVehiclePose(pose, True)


# def get_GPS(client):
#     drone_state = client.getMultirotorState()
#     current_position = drone_state.kinematics_estimated.position
#     return [current_position.x_val, current_position.y_val]

# def calculate_distance(pos1, pos2):
#     dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
#     return dist

# def get_yaw(client):
#     vehicle_pose = client.simGetVehiclePose()
#     orientation = vehicle_pose.orientation
#     orientation_euler = airsim.to_eularian_angles(orientation)
#     yaw_angle_degrees = math.degrees(orientation_euler[2])
#     return yaw_angle_degrees

# def get_desired_yaw(current_pos,desired_pos):
    
#     return math.degrees(math.atan2(desired_pos[1]-current_pos[1],desired_pos[0]-current_pos[0]))

# def translate_desired_yaw(yaw):
#     # Wrap around if outside the acceptable range
#     if yaw < 270:
#         yaw = - (yaw - 90)
#     elif yaw > 270:
#         yaw = 180 - (yaw - 270)
#     return yaw

# # Connect to AirSim 
# # client = airsim.CarClient()
# client = airsim.MultirotorClient()

# client.confirmConnection()
# client.enableApiControl(True)

# client.armDisarm(True)
# client.takeoffAsync().join()

# yaw_error_list = []  # Store yaw_error values for plotting
# forward_velocity = 1.0
# try:
#     while True:
#         current_position = get_GPS(client)
#         current_yaw = get_yaw(client)
#         if calculate_distance(current_position, desired_position) > 1:
#             desired_yaw = get_desired_yaw(current_position, desired_position)
#         else:
#             desired_yaw = current_yaw

#         desired_yaw = translate_desired_yaw(desired_yaw)
#         # Calculate yaw error
#         yaw_error = desired_yaw - current_yaw
#         yaw_error_list.append(yaw_error)  # Append the yaw_error to list
#         delta_error = yaw_error - previous_error
#         integral += yaw_error

#         # PID Controller
#         yaw_rate_command = kp_yaw * yaw_error + ki_yaw * integral + kd_yaw * delta_error
#         previous_error = yaw_error

#         # Send command to drone
#         # z = -2  # Maintain an altitude of 2 meters
#         # duration = 0.1  # Send commands more frequently
#         # yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate_command)
#         # client.moveByVelocityZAsync(forward_velocity * math.cos(math.radians(current_yaw)), forward_velocity * math.sin(math.radians(current_yaw)), z, duration, yaw_mode).join()
#         z = -2  # maintain an altitude of 2 meters. Negative because NED coordinates.
#         forward_velocity = 2  # example speed for moving forward
#         duration = 0.1  # Send commands more frequently
#         yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate_command)

#         # Only move in the X direction (which is the drone's forward direction)
#         client.moveByVelocityZAsync(forward_velocity, 0, z, duration, yaw_mode).join()
#         print("Current position", current_position, "Current yaw", current_yaw, "desired yaw", desired_yaw, "yaw_error", yaw_error)

#         # Stopping condition (when error is small)
#         if calculate_distance(current_position, desired_position) < 0.5:  # Close enough to target
#             break

#         time.sleep(0.2)
# except KeyboardInterrupt:
#     print("\nInterrupted by user. Plotting available data...")

# finally:
#     client.landAsync().join()
#     client.armDisarm(False)
#     client.enableApiControl(False)

#     # Plot yaw_error
#     plt.figure()
#     plt.plot(yaw_error_list)
#     plt.title("Yaw Error Over Time")
#     plt.xlabel("Time (in 0.2s intervals)")
#     plt.ylabel("Yaw Error (in degrees)")
#     plt.show()

# import airsim
# import math
# import numpy as np
# import time
# import matplotlib.pyplot as plt
# kp_yaw = 3
# ki_yaw = 0.01
# kd_yaw = 0.02
# desired_position = [10, 20]

# previous_error = 0
# integral = 0
# def set_yaw_to_zero(client):
#     pose = client.simGetVehiclePose()
#     pitch, roll, _ = airsim.to_eularian_angles(pose.orientation)
#     new_orientation = airsim.to_quaternion(pitch, roll, math.radians(-30))
#     pose.orientation = new_orientation
#     client.simSetVehiclePose(pose, True)


# def get_GPS(client):
#     drone_state = client.getMultirotorState()
#     current_position = drone_state.kinematics_estimated.position
#     return [current_position.x_val, current_position.y_val]

# def calculate_distance(pos1, pos2):
#     dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
#     return dist

# def get_yaw(client):
#     vehicle_pose = client.simGetVehiclePose()
#     orientation = vehicle_pose.orientation
#     orientation_euler = airsim.to_eularian_angles(orientation)
#     yaw_angle_degrees = math.degrees(orientation_euler[2])
#     return yaw_angle_degrees

# def get_desired_yaw(current_pos,desired_pos):
    
#     return math.degrees(math.atan2(desired_pos[1]-current_pos[1],desired_pos[0]-current_pos[0]))

# def translate_desired_yaw(yaw):
#     # Wrap around if outside the acceptable range
#     if yaw < 270:
#         yaw = - (yaw - 90)
#     elif yaw > 270:
#         yaw = 180 - (yaw - 270)
#     return yaw

# # Connect to AirSim 
# # client = airsim.CarClient()
# client = airsim.MultirotorClient()

# client.confirmConnection()
# client.enableApiControl(True)

# client.armDisarm(True)
# client.takeoffAsync().join()

# yaw_error_list = []  # Store yaw_error values for plotting
# forward_velocity = 1.0
# try:
#     while True:
#         current_position = get_GPS(client)
#         current_yaw = get_yaw(client)
#         if calculate_distance(current_position, desired_position) > 1:
#             desired_yaw = get_desired_yaw(current_position, desired_position)
#         else:
#             desired_yaw = current_yaw

#         desired_yaw = translate_desired_yaw(desired_yaw)
#         # Calculate yaw error
#         yaw_error = desired_yaw - current_yaw
#         yaw_error_list.append(yaw_error)  # Append the yaw_error to list
#         delta_error = yaw_error - previous_error
#         integral += yaw_error

#         # PID Controller
#         yaw_rate_command = kp_yaw * yaw_error + ki_yaw * integral + kd_yaw * delta_error
#         previous_error = yaw_error

#         # Send command to drone
#         # z = -2  # Maintain an altitude of 2 meters
#         # duration = 0.1  # Send commands more frequently
#         # yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate_command)
#         # client.moveByVelocityZAsync(forward_velocity * math.cos(math.radians(current_yaw)), forward_velocity * math.sin(math.radians(current_yaw)), z, duration, yaw_mode).join()
#         z = -2  # maintain an altitude of 2 meters. Negative because NED coordinates.
#         forward_velocity = 2  # example speed for moving forward
#         duration = 0.1  # Send commands more frequently
#         yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate_command)

#         # Only move in the X direction (which is the drone's forward direction)
#         client.moveByVelocityZAsync(forward_velocity, 0, z, duration, yaw_mode).join()
#         print("Current position", current_position, "Current yaw", current_yaw, "desired yaw", desired_yaw, "yaw_error", yaw_error)

#         # Stopping condition (when error is small)
#         if calculate_distance(current_position, desired_position) < 0.5:  # Close enough to target
#             break

#         time.sleep(0.2)
# except KeyboardInterrupt:
#     print("\nInterrupted by user. Plotting available data...")

# finally:
#     client.landAsync().join()
#     client.armDisarm(False)
#     client.enableApiControl(False)

#     # Plot yaw_error
#     plt.figure()
#     plt.plot(yaw_error_list)
#     plt.title("Yaw Error Over Time")
#     plt.xlabel("Time (in 0.2s intervals)")
#     plt.ylabel("Yaw Error (in degrees)")
#     plt.show()
import airsim
import time

# Connect to AirSim
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

# Take off
client.takeoffAsync().join()

# Move to a desired position
x = 0  # in meters
y = 5  # in meters
z = -2  # in meters (Note: AirSim uses NED coordinates, so negative values indicate an altitude above the starting point)
velocity = 3  # in m/s, this is the maximum velocity
client.moveToPositionAsync(x, y, z, velocity).join()

# Change drone's orientation to face a desired direction
desired_yaw_deg = 180  # for example, facing east (Note: 0 deg = North, 90 deg = East, 180 deg = South, -90 or 270 deg = West)
yaw_rate = 30  # speed at which the drone turns, in degrees per second
duration = abs(desired_yaw_deg) / yaw_rate  # time taken to reach the desired yaw
client.rotateByYawRateAsync(yaw_rate if desired_yaw_deg > 0 else -yaw_rate, duration).join()

# Hover for a specified duration
hover_duration = 10  # seconds
client.hoverAsync().join()
time.sleep(hover_duration)

# Land the drone
client.landAsync().join()

client.armDisarm(False)
client.enableApiControl(False)


# ready to run example: PythonClient/car/hello_car.py
import airsim
import time
import numpy as np
import os
import math
# connect to the AirSim simulator
client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
car_controls = airsim.CarControls()

def get_gps(client):
    client.simPause(True)
    gps_data = client.getGpsData()
    client.simPause(False)
    return gps_data.gnss.geo_point.latitude,gps_data.gnss.geo_point.longitude

def get_image(client):
    # get camera images from the car
    camera_names=["left_camera","front_center","right_camera"]
    responses = client.simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])
    for i,response in enumerate(responses):
        # get numpy array
        img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8) 
        # reshape array to 4 channel image array H X W X 4
        img_rgb = img1d.reshape(response.height, response.width, 3)
        # write to png 
        airsim.write_png(os.path.normpath("image_" +camera_names[i]+ '.png'), img_rgb) 

def get_yaw(client):
    vehicle_pose = client.simGetVehiclePose()
    orientation = vehicle_pose.orientation
    orientation_euler = airsim.to_eularian_angles(orientation)
    yaw_angle_degrees = math.degrees(orientation_euler[2])
    return yaw_angle_degrees

# set the controls for car
car_controls.throttle = 1
car_controls.steering = 0.5
while True:
    # get state of the car
    car_state = client.getCarState()
    yaw = get_yaw(client)
    print("Speed %d, Gear %d, Yaw:%d" % (car_state.speed, car_state.gear,yaw))
    client.setCarControls(car_controls)

    # let car drive a bit
    time.sleep(1)
    get_image(client)
    gps=get_gps(client)
    print(gps)
    
    # Calculate the steering input (adjust this control law as needed)
    steering_gain = 0.1  # Proportional gain
    yaw=get_yaw(client)
    steering = steering_gain * (60 - yaw)

    # Ensure the steering input is within valid bounds (-1.0 to 1.0)
    steering = max(min(steering, 1.0), -1.0)
    print(steering)

import airsim
import os
import math
import numpy as np

def get_yaw(client):
    vehicle_pose = client.simGetVehiclePose()
    orientation = vehicle_pose.orientation
    orientation_euler = airsim.to_eularian_angles(orientation)
    yaw_angle_degrees = math.degrees(orientation_euler[2])
    return yaw_angle_degrees

def get_position(client):
    vehicle_pose = client.simGetVehiclePose()
    position = vehicle_pose.position
    return position.x_val, position.y_val, position.z_val


def get_image(client):
    # get camera images from the car
    # client.simPause(False)
    camera_names=["left_camera","front_center","right_camera"]
    responses = client.simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])
    # client.simPause(True)
    for i,response in enumerate(responses):
        # get numpy array
        img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8) 
        # reshape array to 4 channel image array H X W X 4
        img_rgb = img1d.reshape(response.height, response.width, 3)
        # write to png 
        airsim.write_png(os.path.normpath("image_" +camera_names[i]+ '.png'), img_rgb) 
    return  ['image_front_center.png','image_left_camera.png','image_right_camera.png']



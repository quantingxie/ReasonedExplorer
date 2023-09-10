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


def get_image(client, step_counter):
    camera_names = ["right_camera", "front_center", "left_camera"]
    responses = client.simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])

    saved_images = []
    for i, response in enumerate(responses):
        # get numpy array
        img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8) 
        # reshape array to 4 channel image array H X W X 4
        img_rgb = img1d.reshape(response.height, response.width, 3)
        # write to png with step count in the name
        image_name = os.path.normpath(f"step_{step_counter}_image_{camera_names[i]}.png")
        airsim.write_png(image_name, img_rgb)
        saved_images.append(image_name)
        
    return saved_images

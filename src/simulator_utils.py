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


def get_image(client, step_counter, experiment_name="default_experiment"):
    import os
    
    camera_names = ["right_camera", "front_center", "left_camera"]
    responses = client.simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])

    # Create an experiment-specific directory to save the images
    directory = os.path.normpath(f"saved_images/{experiment_name}")
    if not os.path.exists(directory):
        os.makedirs(directory)

    saved_images = []
    for i, response in enumerate(responses):
        # get numpy array
        img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
        # reshape array to 4 channel image array H X W X 4
        img_rgb = img1d.reshape(response.height, response.width, 3)
        
        # write to png with step count in the name, saving inside the experiment-specific folder
        image_name = os.path.normpath(f"{directory}/step_{step_counter}_image_{camera_names[i]}.png")
        airsim.write_png(image_name, img_rgb)
        saved_images.append(image_name)
        
    return saved_images


def compute_euclidean_distances_from_current_sim(current_node_gps, nodes_gps_list):
    """Compute the Euclidean distances from the current node to all other nodes in the list."""
    
    def euclidean_distance(coord1, coord2):
        """Calculate the Euclidean distance between two coordinates."""
        # print("Coord1:", coord1)
        # print("Coord2:", coord2)

        x1, y1, _ = coord1
        x2, y2 = coord2  # Assuming the second coordinate might have an extra value (like altitude) that we want to ignore.
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    return [euclidean_distance(current_node_gps, node_gps) for node_gps in nodes_gps_list]
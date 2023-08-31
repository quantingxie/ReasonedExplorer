import math
import time
from capture_image import capture_image_at_angle
import robot_interface as sdk
from VLM import VLM_query

HIGHLEVEL = 0xee
udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
cmd = sdk.HighCmd()
state = sdk.HighState()
udp.InitCmdData(cmd)

def capture_images_by_rotate(n: int, range_of_motion=20) -> list:
    captured_images = []

    # Convert range_of_motion to radians
    range_of_motion_radians = math.radians(range_of_motion)

    # Calculate min_angle and max_angle based on range_of_motion in radians
    min_angle = -range_of_motion_radians / 2
    print("min_angle",min_angle)
    # Calculate the angle increment in radians
    angle_increment = range_of_motion_radians / n
    print("increment", angle_increment)
    # Capture images while rotating from the left to right (from min_angle to max_angle)
    for i in range(n):
        yaw_angle = min_angle + i * angle_increment

        cmd.euler = [0, 0, yaw_angle]
        cmd.mode = 1

        udp.SetSend(cmd)
        udp.Send()
        time.sleep(1000)

        angle_in_degrees = math.degrees(yaw_angle)
        print("current angle",angle_in_degrees)
        image = capture_image_at_angle(angle_in_degrees)
        if image is not None:
            captured_images.append(image)

    # Reset the robot's position after capturing all images
    cmd.euler = [0, 0, 0]
    udp.SetSend(cmd)
    udp.Send()

    return captured_images

n = 5
rom = 70

captured_images = capture_images_by_rotate(n, rom)

curr_nodes_data = []
reached_goal = False
for image in captured_images:
    description, found = VLM_query(image)
    curr_nodes_data.append((description, found))

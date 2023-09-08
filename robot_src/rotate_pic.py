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

    # Calculate min_angle based on range_of_motion in radians
    min_angle = -range_of_motion_radians / 2

    # Calculate the angle increment in radians
    angle_increment = range_of_motion_radians / n

    # Initialize motion time and yaw angle
    motiontime = 0
    yaw_angle = min_angle

    while motiontime < n+1:
        time.sleep(0.01)
        motiontime += 1

        # Receive current state (Not necessary for your function, but kept for compatibility)
        udp.Recv()
        udp.GetRecv(state)

        # Set mode and euler angles for the robot
        cmd.mode = 1
        cmd.euler = [0, 0, yaw_angle]

        # Send the udp command
        udp.SetSend(cmd)
        udp.Send()

        # Capture image and append it if it's not None
        angle_in_degrees = math.degrees(yaw_angle)
        image = capture_image_at_angle(angle_in_degrees)
        if image is not None:
            captured_images.append(image)

        # Update the yaw_angle for the next iteration
        yaw_angle += angle_increment

    return captured_images

n = 2
rom = 50

captured_images = capture_images_by_rotate(n, rom)

curr_nodes_data = []
reached_goal = False
for image in captured_images:
    description, found = VLM_query(image)
    curr_nodes_data.append((description, found))

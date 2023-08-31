import robot_interface as sdk
import math  # Importing the math module

HIGHLEVEL = 0xee

yaw_angle_degrees = 2
yaw_angle_radians = math.radians(yaw_angle_degrees)  # Convert the yaw angle from degrees to radians

udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
cmd = sdk.HighCmd()
state = sdk.HighState()
udp.InitCmdData(cmd)

cmd.euler = [0, 0, yaw_angle_radians]  # Use the radians value
cmd.mode = 1

udp.SetSend(cmd)
udp.Send()
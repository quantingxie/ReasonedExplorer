HIGHLEVEL = 0xee
import robot_interface as sdk


yaw_angle = 2


udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
cmd = sdk.HighCmd()
state = sdk.HighState()
udp.InitCmdData(cmd)

cmd.euler = [0, 0, yaw_angle]
cmd.mode = 1

udp.SetSend(cmd)
udp.Send()
import airsim
import time
import math

def get_yaw(client):
    vehicle_pose = client.simGetVehiclePose()
    orientation = vehicle_pose.orientation
    orientation_euler = airsim.to_eularian_angles(orientation)
    car_state = client.getCarState()
    current_position = car_state.kinematics_estimated.position
    print("car state kinematics: ",current_position)
    print("orientation: ", orientation)
    yaw_angle_degrees = math.degrees(orientation_euler[2])
    return yaw_angle_degrees

# Connect to AirSim 
client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
# Get car controls
car_controls = airsim.CarControls()
car_controls.is_manual_gear = False  # automatic gear
car_controls.steering = -0.5  # start with half left turn as an example
car_controls.throttle = 1  # some forward motion to help with the turn

# before
car_state = client.getCarState()
yaw=get_yaw(client)
print("Speed %d, Gear %d, Yaw:%d" % (car_state.speed, car_state.gear,yaw))

client.setCarControls(car_controls)
time.sleep(3)  # let the car turn for 1 second; adjust as needed for your desired turn

# Stop the car
car_controls.steering = 0
car_controls.throttle = 0
client.setCarControls(car_controls)
# after
car_state = client.getCarState()
yaw=get_yaw(client)
print("Speed %d, Gear %d, Yaw:%d" % (car_state.speed, car_state.gear,yaw))

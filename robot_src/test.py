import math

current_pos = [40.44364583, -79.944248]
waypoint = [40.443669, -79.944086]

dlat = waypoint[0] - current_pos[0]
dlon = waypoint[1] - current_pos[1]

desired_yaw = math.atan2(dlat, dlon)
desired_yaw = desired_yaw - math.pi/2  # Adjust for North as 0

# Wrap the angle between -pi to pi
desired_yaw = (desired_yaw + math.pi) % (2 * math.pi) - math.pi

print(math.degrees(desired_yaw))

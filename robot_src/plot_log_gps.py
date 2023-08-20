import numpy as np
from pyproj import Transformer, CRS

# load the data
data = np.loadtxt('send_gps_data_log.txt', delimiter=',')

def convert_relative_to_gps(latitudes, longitudes):
    # Define the coordinate systems
    wgs84 = CRS('EPSG:4326')  # WGS84 geographic CRS (lat/lon)
    utm = CRS('EPSG:32632')  # Or whatever UTM zone is relevant

    # Convert initial point to UTM
    transformer_to_utm = Transformer.from_crs(wgs84, utm)

    x, y = transformer_to_utm.transform(latitudes, longitudes)

    return x, y

def convert_relative_to_gps_manual(latitudes, longitudes, lat0, lon0):
    R = 6371e3  # Earth radius in meters
    phi1 = np.radians(lat0)
    phi2 = np.radians(latitudes)
    delta_phi = np.radians(latitudes - lat0)
    delta_lambda = np.radians(longitudes - lon0)

    x = delta_lambda * np.cos((phi1 + phi2)/2)
    y = delta_phi

    return x * R, y * R

# Separate latitudes and longitudes for clarity
latitudes = data[:, 0]
longitudes = data[:, 1]

lat0 = latitudes[0]
lon0 = longitudes[0]

xm, ym = convert_relative_to_gps_manual(latitudes, longitudes, lat0, lon0)
# Convert latitude and longitude to UTM
x, y = convert_relative_to_gps(latitudes, longitudes)

# plot the data
import matplotlib.pyplot as plt
# plt.figure(figsize=(10, 8))
# # plt.plot(x, y, 'o')
# plt.plot(x, y, 'o')
# plt.title('Plot of UTM coordinates')
# plt.xlabel('X (meters)')
# plt.ylabel('Y (meters)')
# plt.show()

# Calculate the maximum distance from the origin (0,0) in both x and y directions
max_dist = max(np.max(np.abs(xm)), np.max(np.abs(ym)))

# Add 10% padding
max_dist *= 1.1

# Plot the data
plt.figure(figsize=(10, 8))
plt.plot(xm, ym, 'o', label='Data Points')
plt.plot(0, 0, 'ro', label='Initial Lat and Lon')  # This line plots the reference point
plt.xlim(-max_dist, max_dist)  # set the x-axis limits
plt.ylim(-max_dist, max_dist)  # set the y-axis limits
plt.title('Plot of Cartesian coordinates')
plt.xlabel('X (meters)')
plt.ylabel('Y (meters)')
plt.legend()
plt.grid(True)
plt.show()
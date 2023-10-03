import numpy as np
import math
import gmplot

def visualize_exploration_on_map(explorer, filename="exploration_map.html"):
    # Assuming the first GPS data point to center the map
    lat0, lon0 = explorer.nodes[0][2]  # extracting GPS data from the first node

    gmap_exploration = gmplot.GoogleMapPlotter(lat0, lon0, 19)
    gmap_exploration.apikey = "AIzaSyC9vS1own2-T3scUJPZdefXLYBnUQr1pSE"  # replace with your API key
    gmap_exploration.map_type = "satellite"

    # Add nodes to the map
    for node in explorer.nodes:
        data, bounding_box, gps_data = node
        lat, lon = gps_data
        # Since all nodes in explorer.nodes are explored, we'll color them green
        gmap_exploration.circle(lat, lon, 3, color='green')

    # Connect nodes to show the path of exploration
    for i in range(len(explorer.nodes) - 1):
        lat1, lon1 = explorer.nodes[i][2]   # GPS data of the current node
        lat2, lon2 = explorer.nodes[i + 1][2]  # GPS data of the next node
        gmap_exploration.plot([lat1, lat2], [lon1, lon2], 'blue', edge_width=2.5)

    # Save the map to an HTML file
    gmap_exploration.draw(filename)
    

def meters_to_lat(meters):
    return meters / 111320

def meters_to_lon(meters, latitude):
    # Conversion factor based on latitude for longitude
    m_per_deg = 111320 * math.cos(math.radians(latitude))
    return meters / m_per_deg

def lat_to_meters(lat_diff):
    # approximate radius of earth in km
    R = 6378.1 
    return R * lat_diff * (math.pi / 180) * 1000

def lon_to_meters(lon_diff, lat):
    # approximate radius of earth in km
    R = 6378.1
    return R * lon_diff * (math.pi / 180) * math.cos(lat * math.pi/180) * 1000


def compute_euclidean_distances_from_current(current_node_gps, nodes_gps_list):
    """Compute the Euclidean distances from the current node to all other nodes in the list."""
    
    def euclidean_distance(coord1, coord2):
        """Calculate the Euclidean distance between two coordinates."""
        # print("Coord1:", coord1)
        # print("Coord2:", coord2)

        x1, y1 = coord1
        x2, y2 = coord2  # Assuming the second coordinate might have an extra value (like altitude) that we want to ignore.
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    return [euclidean_distance(current_node_gps, node_gps) for node_gps in nodes_gps_list]

def compute_euclidean_distance(coord1, coord2):
    """Calculate the Euclidean distance between two coordinates."""
    x1, y1, _ = coord1
    x2, y2 = coord2  # Also capture the possible third component, though it's ignored in the computation.
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def sigmoid_modulated_distance(d, k, d0):
    """Computes the sigmoid-modulated distance for a given distance."""
    return 1 / (1 + math.exp(-k * (d - d0)))
import networkx as nx
import math

class GraphManager:
    def __init__(self):
        self.graph = nx.Graph()
        self.current_node_id = 0

    def add_node(self, position, yaw, score, embedding):
        # Adds a node to the graph with the given position, yaw, score, and description.
        self.graph.add_node(self.current_node_id, position=position, yaw=yaw, score=score, embedding=embedding)
        self.current_node_id += 1
        return self.current_node_id - 1

    def add_edge(self, node1_id, node2_id):
        # Adds an edge between two nodes in the graph.
        self.graph.add_edge(node1_id, node2_id)

    def find_lowest_score_node(self):
        # Finds the node with the lowest score.
        min_score = float('inf')
        min_node_id = None
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data['score'] < min_score:
                min_score = node_data['score']
                min_node_id = node_id
        return min_node_id


# def expand_node_in_directions(graph_manager, current_position, current_yaw, scores, descriptions):
#     directions = [30, 90, 120]  # Angles in degrees
#     fixed_length = 1  # Replace with the actual length of each step.
#     concatenated_description = ' '.join(descriptions)  # Concatenate descriptions for the current node

#     current_node_id = graph_manager.add_node(current_position, current_yaw, 0, concatenated_description)  # Assuming current node has a score of 0

#     for angle, score in zip(directions, scores):
#         new_yaw = current_yaw + math.radians(angle)
#         new_position = (current_position[0] + fixed_length * math.cos(new_yaw),
#                         current_position[1] + fixed_length * math.sin(new_yaw))

#         # Generate the description for the new node in the given direction
#         new_description = generate_description_for_direction(angle)  # Implement this function based on your requirements

#         # Add the new node to the graph with the calculated position, yaw, score, and description
#         new_node_id = graph_manager.add_node(new_position, new_yaw, score, new_description)
#         graph_manager.add_edge(current_node_id, new_node_id)

#     return graph_manager

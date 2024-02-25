import networkx as nx
import math
import matplotlib.pyplot as plt


class GraphManager:
    def __init__(self):
        self.graph = nx.Graph()
        self.current_node_id = 0
        # self.add_node(position=(0, 0), yaw=0, score=0, embedding=None)

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

    def visualize_graph(self, show_labels=True, save_path=None):
        """
        Visualizes the graph with nodes and edges.
        Option to show labels with node scores and positions, and to save the visualization to a file.
        """
        plt.figure(figsize=(15, 15))  # Set the figure size (optional)
        pos = {node: (data['position'][0], data['position'][1]) for node, data in self.graph.nodes(data=True)}
        labels = {node: f"ID: {node}\nScore: {data['score']}" for node, data in self.graph.nodes(data=True)} if show_labels else None
        # Draw nodes
        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=700, font_size=10)
        # Draw node labels (e.g., scores)
        if labels:
            nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos)

        plt.gca().set_aspect('equal', adjustable='box')
        plt.title("Graph Visualization")
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.tight_layout()


        if save_path:
            plt.savefig(save_path) 

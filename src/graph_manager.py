import networkx as nx
import math
import matplotlib.pyplot as plt


class GraphManager:
    def __init__(self):
        self.graph = nx.Graph()
        self.current_node_id = 0

    def add_node(self, position, yaw, score, embedding):
        # Adds a node to the graph with the given position, yaw, score, and description.
        self.graph.add_node(self.current_node_id, position=position, yaw=yaw, score=score, embedding=embedding)
        self.current_node_id += 1
        print(self.current_node_id)
        return self.current_node_id - 1

    def add_edge(self, node1_id, node2_id):
        # Adds an edge between two nodes in the graph.
        self.graph.add_edge(node1_id, node2_id)

    def mark_node_as_visited(self, node_id):
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id]['visited'] = True
            
    def find_highest_score_unvisited_node(self):
        max_score = -float('inf')  # Start with the smallest possible number
        max_node_id = None
        for node_id, node_data in self.graph.nodes(data=True):
            if not node_data.get('visited', False) and node_data['score'] > max_score:
                max_score = node_data['score']
                max_node_id = node_id
        return max_node_id

    def find_shortest_path_to_highest_score_node(self, start_node_id):
        # Finds the shortest path from the given start node to the node with the highest score.
        target_node_id = self.find_highest_score_unvisited_node()
        if target_node_id is None:
            return None  # No target node found
        try:
            path = nx.shortest_path(self.graph, source=start_node_id, target=target_node_id)
            return path
        except nx.NetworkXNoPath:
            return None  # No path found

    # def visualize_graph(self, show_labels=True, save_path=None):
    #     """
    #     Visualizes the graph with nodes and edges.
    #     Option to show labels with node scores and positions, and to save the visualization to a file.
    #     """
    #     plt.figure(figsize=(15, 15))  # Set the figure size (optional)
    #     pos = {node: (data['position'][0], data['position'][1]) for node, data in self.graph.nodes(data=True)}
    #     labels = {node: f"ID: {node}\nScore: {data['score']}" for node, data in self.graph.nodes(data=True)} if show_labels else None
    #     # Draw nodes
    #     nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=700, font_size=10)
    #     # Draw node labels (e.g., scores)
    #     if labels:
    #         nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
    #     # Draw edges
    #     nx.draw_networkx_edges(self.graph, pos)

    #     plt.gca().set_aspect('equal', adjustable='box')
    #     plt.title("Graph Visualization")
    #     plt.xlabel("X Position")
    #     plt.ylabel("Y Position")
    #     plt.tight_layout()


    #     if save_path:
    #         plt.savefig(save_path) 
    def visualize_graph(self, path=None, show_labels=True, save_path=None):
        plt.figure(figsize=(15, 15))  # Set the figure size (optional)
        pos = {node: (data['position'][0], data['position'][1]) for node, data in self.graph.nodes(data=True)}
        labels = {node: f"ID: {node}\nScore: {data['score']}" for node, data in self.graph.nodes(data=True)} if show_labels else None
        
        # Separate nodes by visited status
        visited_nodes = [node for node, data in self.graph.nodes(data=True) if data.get('visited', False)]
        unvisited_nodes = [node for node, data in self.graph.nodes(data=True) if not data.get('visited', False)]
        
        # Draw unvisited nodes
        nx.draw_networkx_nodes(self.graph, pos, nodelist=unvisited_nodes, node_color='lime', node_size=700)
        # Draw visited nodes
        nx.draw_networkx_nodes(self.graph, pos, nodelist=visited_nodes, node_color='hotpink', node_size=900)
        
        # Draw edges (make lines thicker by increasing the width)
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', width=3)
        
        # Draw node labels if enabled
        if labels:
            nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        
        # Highlight the path if provided
        if path:
            # Extract edges from the path
            path_edges = list(zip(path, path[1:]))
            # Draw the path edges
            nx.draw_networkx_edges(self.graph, pos, edgelist=path_edges, edge_color='red', width=4)
            
            # Highlight the path nodes
            nx.draw_networkx_nodes(self.graph, pos, nodelist=path, node_color='red', node_size=700)
            
            # Specifically highlight the goal node if you want it to stand out
            goal_node = path[-1] 
            nx.draw_networkx_nodes(self.graph, pos, nodelist=[goal_node], node_color='red', node_size=900) 
            
        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        # Remove the box around the graph
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        # plt.show()  # Show the plot as well
import networkx as nx
import heapq


def create_maximal_graph(option_map):
    """
    Create a directed graph from the option_map.
    
    Parameters:
        option_map (dict): Dictionary representing the grid.
                          Keys are (x, y) positions, and values are dictionaries
                          of directions ('up', 'down', 'left', 'right') mapped to weights.

    Returns:
        graph (nx.DiGraph): A directed graph representing the grid.
    """
    graph = nx.DiGraph()
    for position, options in option_map.items():
        graph.add_node(position)  # Add position as a node
        for direction, weight in options.items():
            # Determine the neighboring position based on the direction
            if direction == 'up':
                neighbor = (position[0], position[1] + 1)
            elif direction == 'down':
                neighbor = (position[0], position[1] - 1)
            elif direction == 'left':
                neighbor = (position[0] - 1, position[1])
            elif direction == 'right':
                neighbor = (position[0] + 1, position[1])
            else:
                continue  # Skip invalid directions

            # Add edge with weight
            graph.add_edge(position, neighbor, weight=weight)
    return graph


def dijkstra(graph, start, goal):
    """
    Implementation of Dijkstra's algorithm for shortest path.
    
    Parameters:
        graph (nx.DiGraph): Directed graph with weighted edges.
        start (tuple): Starting node (x, y).
        goal (tuple): Goal node (x, y).
    
    Returns:
        list: List of nodes representing the shortest path from start to goal.
              Returns an empty list if no path is found.
    """
    frontier = []  # Priority queue (min-heap)
    visited = set()  # Keep track of visited nodes
    came_from = {}  # To reconstruct the path
    cost = {node: float('inf') for node in graph.nodes}  # Cost from start to each node
    cost[start] = 0  # Cost of start node is zero

    # Push start node into the priority queue
    heapq.heappush(frontier, (cost[start], start))

    while frontier:
        # Pop the node with the lowest cost
        _, current_node = heapq.heappop(frontier)

        # Stop if we've reached the goal
        if current_node == goal:
            path = []
            while current_node != start:
                path.append(current_node)
                current_node = came_from[current_node]
            # path.append(start) Esto hace que la lista contenga el inicio y coincida el inicio.
            return path[::-1]  # Reverse the path to get start-to-goal order

        visited.add(current_node)

        # Explore neighbors
        for neighbor in graph.neighbors(current_node):
            if neighbor in visited:
                continue

            # Calculate the cost to reach the neighbor
            tentative_cost = cost[current_node] + graph.get_edge_data(current_node, neighbor)['weight']
            if tentative_cost < cost[neighbor]:
                came_from[neighbor] = current_node
                cost[neighbor] = tentative_cost
                heapq.heappush(frontier, (tentative_cost, neighbor))

    # Return an empty list if no path is found
    return []

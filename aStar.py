import networkx as nx
import heapq
from map import optionMap

""" Get a list of intermediate steps between two points on the grid """
def get_intermediate_steps(origin, goal):
    # Calculate differences in x and y coordinates
    diff_x = goal[0] - origin[0]
    diff_y = goal[1] - origin[1]

    # Determine the number of steps needed for each axis
    num_steps_x = abs(diff_x)
    num_steps_y = abs(diff_y)

    # Calculate the increment values for each step on x and y axes
    increment_x = diff_x // num_steps_x if num_steps_x else 0
    increment_y = diff_y // num_steps_y if num_steps_y else 0

    # Generate the intermediate steps
    intermediate_steps = []
    current_step = origin
    for _ in range(max(num_steps_x, num_steps_y)):
        x = current_step[0] + increment_x
        y = current_step[1] + increment_y
        current_step = (x, y)
        intermediate_steps.append(current_step)

    return intermediate_steps

""" Define Manhattan distance heuristic """
def manhattan_distance(node, goal):
    return abs(goal[0] - node[0]) + abs(goal[1] - node[1])

""" Create the problem directed graph """
def create_graph(IntersectionPoints):
    graph = nx.DiGraph()
    for node, connections in IntersectionPoints.items():
        for neighbor, cost in connections.items():
            graph.add_edge(node, neighbor, weight=cost)
    return graph

""" Create the problem directed graph of all the grid"""
def create_maximal_graph(OptionMap):
    graph = nx.DiGraph()
    for position, options in OptionMap.items():
        graph.add_node(position)
        for direction, weight in options.items():
            if direction == 'up':
                graph.add_edge(position, (position[0], position[1] + 1), weight=weight)
            elif direction == 'down':
                graph.add_edge(position, (position[0], position[1] - 1), weight=weight)
            elif direction == 'left':
                graph.add_edge(position, (position[0] - 1, position[1]), weight=weight)
            elif direction == 'right':
                graph.add_edge(position, (position[0] + 1, position[1]), weight=weight)
    return graph

""" A* algorithm implementation using Manhattan distance as a heuristic """
def astar(graph, start, goal, heuristic):
    frontier = [(0, start)]
    heapq.heapify(frontier)
    came_from = {}
    cost_so_far = {start: 0}

    while frontier:
        current_cost, current_node = heapq.heappop(frontier)

        if current_node == goal:
            break

        for next_node in graph.neighbors(current_node):
            new_cost = cost_so_far[current_node] + graph[current_node][next_node]['weight']
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(next_node, goal)
                heapq.heappush(frontier, (priority, next_node))
                came_from[next_node] = current_node

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()

    # Get intermediate steps
    full_path = []
    for i in range(len(path) - 1):
        full_path.extend(get_intermediate_steps(path[i], path[i + 1]))

    return full_path

""" A* algorithm implementation using Manhattan distance as a heuristic
    It is adapted to search through all the grid.
 """
def astarComplete(graph, start, goal, heuristic):
    # Priority Queue/ Min Heap
    frontier = []
    # Set to keep track of visited nodes
    visited = set()
    # To store predecessos
    came_from = {}
    # Dictionary of costs from start to each node
    cost = {node: float('inf') for node in graph.nodes}
    cost[start] = 0

    # push start node
    heapq.heappush(frontier, (cost[start], start))

    while frontier:
        _, current_node = heapq.heappop(frontier)


        if current_node == goal:
            path = []
            while current_node != start:
                path.append(current_node)
                current_node = came_from[current_node]
            return path[::-1]


        visited.add(current_node)

        for neighbor_node in graph.neighbors(current_node):
            if neighbor_node in visited:
                continue

            tentative_cost = cost[current_node] + graph.get_edge_data(current_node, neighbor_node)['weight']
            if tentative_cost < cost[neighbor_node]:
                came_from[neighbor_node] = current_node
                cost[neighbor_node] = tentative_cost

                priority = tentative_cost + heuristic(neighbor_node, goal)
                heapq.heappush(frontier, (priority, neighbor_node))

    return []
import math
import heapq
from graph_utils import build_graph, modes_speed, load_data

#tính khoảng cách đường chim bay
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamba = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamba / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

def a_star(graph, nodes, start, goal, mode):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: haversine(*nodes[start], *nodes[goal]) / modes_speed[mode]}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current), g_score[current]
        
        for edge in graph.get(current, []):
            neighbor = edge["neighbor"]
            if mode not in edge["allowed"]:
                continue
            cost = edge["time"][mode]
            tentative_g = g_score[current] + cost

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + haversine(*nodes[neighbor], *nodes[goal]) / modes_speed[mode]
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, float("inf")

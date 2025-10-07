import math
import heapq
from math import inf
from graph_utils import modes_speed

# Tính khoảng cách đường chim bay
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
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
    dist_score = {start: 0}
    f_score = {start: haversine(*nodes[start], *nodes[goal]) / modes_speed[mode]}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current), g_score[current], dist_score[current], True

        for edge in graph.get(current, []):
            neighbor = edge["neighbor"]

            # Nếu phương tiện không được đi
            if mode not in edge["allowed"]:
                continue

            # Nếu đường bị cấm -> bỏ qua
            if edge.get("traffic") == "blocked":
                continue

            # Điều chỉnh chi phí theo tình trạng giao thông
            traffic = edge.get("traffic", "free")
            traffic_factor = 1.0
            if traffic == "medium":
                traffic_factor = 1.3   # đi chậm hơn 30%
            elif traffic == "heavy":
                traffic_factor = 1.6   # đi chậm hơn 60%

            cost_time = edge["time"][mode] * traffic_factor
            cost_dist = edge["length"]
            tentative_g = g_score[current] + cost_time
            tentative_dist = dist_score[current] + cost_dist

            if tentative_g < g_score.get(neighbor, inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                dist_score[neighbor] = tentative_dist
                f_score[neighbor] = tentative_g + haversine(*nodes[neighbor], *nodes[goal]) / modes_speed[mode]
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, float("inf"), float("inf"), False

import json
import copy
import osmnx as ox
from shapely.geometry import Point, Polygon

modes_speed = {
    "walk": 1.4,
    "bicycle": 4.1,
    "motorcycle": 8.3,
    "car": 11.1
}

restricted_zones = []
flood_zones = []

def load_data(nodes_file="nodes.json", edges_file="edges.json"):
    with open(nodes_file, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    
    with open(edges_file, "r", encoding="utf-8") as f:
        edges = json.load(f)
    
    return nodes, edges

def build_graph(edges):
    graph = {}
    for u, v, length in edges:
        u, v = str(u), str(v)
        graph.setdefault(u, []).append({
            "neighbor": v,
            "length": length,
            "time": {mode: length / speed for mode, speed in modes_speed.items()},
            "allowed": set(modes_speed.keys()),
            "traffic": "free"   # mặc định là đường thông thoáng
        })
    return graph

def nearest_node(G, lon, lat):
    return ox.distance.nearest_nodes(G, lon, lat)

# Chức năng admin

def set_oneway(graph, u, v):
    # Giữ u->v, xóa v->u
    graph[u] = [e for e in graph[u] if e["neighbor"] == v]
    graph[v] = [e for e in graph[v] if e["neighbor"] != u]

def block_edge(graph, u, v, mode):
    for e in graph[u]:
        if e["neighbor"] == v:
            e["allowed"].discard(mode)

def traffic_jam(graph, u, v, factor=5):
    for e in graph[u]:
        if e["neighbor"] == v:
            for m in e["time"]:
                e["time"][m] *= factor

def add_restricted_zone(coords):
    try:
        poly = Polygon([(lon, lat) for lat, lon in coords])  # shapely dùng (x=lon, y=lat)
        restricted_zones.append(poly)
        return True
    except Exception as e:
        print("Lỗi khi thêm vùng cấm:", e)
        return False
    
def add_flood_zone(coords):
    try:
        poly = Polygon([(lon, lat) for lat, lon in coords])
        flood_zones.append(poly)
        return True
    except Exception as e:
        print("Lỗi khi thêm vùng ngập:", e)
        return False
    
def is_in_restricted_zone(lat, lon):
    try:
        p = Point(lon, lat)
        return any(p.within(zone) for zone in restricted_zones)
    except Exception:
        return False


def is_in_flood_zone(lat, lon):
    try:
        p = Point(lon, lat)
        return any(p.within(zone) for zone in flood_zones)
    except Exception:
        return False

def unblock_edge(graph, u, v, mode, length=None):
    for e in graph.get(u, []):
        if e["neighbor"] == v:
            e["allowed"].add(mode)
            return
    # nếu edge bị xóa hẳn thì thêm lại (cần length)
    if length:
        graph.setdefault(u, []).append({
            "neighbor": v,
            "length": length,
            "time": {m: length / spd for m, spd in modes_speed.items()},
            "allowed": set([mode])
        })

def unset_oneway(graph, u, v, length):
    if not any(e["neighbor"] == u for e in graph.get(v, [])):
        graph.setdefault(v, []).append({
            "neighbor": u,
            "length": length,
            "time": {m: length / spd for m, spd in modes_speed.items()},
            "allowed": set(modes_speed.keys())
        })

def reset_graph(original_edges):
    return build_graph(original_edges)

def clone_graph(graph):
    return copy.deepcopy(graph)

def clear_zones():
    restricted_zones.clear()
    flood_zones.clear()
import json
import copy
import osmnx as ox

modes_speed = {
    "walk": 1.4,
    "bicycle": 4.1,
    "motorcycle": 8.3,
    "car": 11.1
}

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

def flood_area(graph, flooded_nodes):
    for u in flooded_nodes:
        graph.pop(u, None)
    for u in list(graph.keys()):
        graph[u] = [e for e in graph[u] if e["neighbor"] not in flooded_nodes]

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
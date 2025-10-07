from flask import Flask, request, jsonify, render_template
import osmnx as ox
from graph_utils import load_data, build_graph
from a_star import a_star

app = Flask(__name__)

place = "O Cho Dua Ward, Hanoi, Vietnam"
G = ox.graph_from_place(place, network_type="all")

nodes_raw, edges_raw = load_data()

nodes = {str(k): (float(v[0]), float(v[1])) for k, v in nodes_raw.items()}

normalized_edges = []
for e in edges_raw:
    if isinstance(e, dict):
        if "u" in e and "v" in e and "length" in e:
            normalized_edges.append((e["u"], e["v"], e["length"]))
        elif "from" in e and "to" in e and "length" in e:
            normalized_edges.append((e["from"], e["to"], e["length"]))
        else:
            raise ValueError(f"Edge dict không có keys mong đợi: {e.keys()}")
    elif isinstance(e, (list, tuple)) and len(e) >= 3:
        normalized_edges.append((e[0], e[1], e[2]))
    else:
        raise ValueError(f"Edge format không hợp lệ: {e}")

graph = build_graph(normalized_edges)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

# API tìm đường cho user
@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    start = payload.get("start")
    goal = payload.get("goal")
    mode = payload.get("mode", "motorcycle")

    if not (isinstance(start, (list, tuple)) and isinstance(goal, (list, tuple))):
        return jsonify({"success": False, "message": "Dữ liệu start/goal sai định dạng"}), 400

    start_lat, start_lng = float(start[0]), float(start[1])
    goal_lat, goal_lng = float(goal[0]), float(goal[1])

    start_node = str(ox.distance.nearest_nodes(G, start_lng, start_lat))
    goal_node  = str(ox.distance.nearest_nodes(G, goal_lng, goal_lat))

    path_nodes, time_cost, dist_cost, _ = a_star(graph, nodes, start_node, goal_node, mode)

    if not path_nodes:
        return jsonify({
            "success": False,
            "message": "Không tìm được đường",
            "path": [],
            "edges": [],
            "time_minutes": None,
            "distance_km": None
        })

    # Tạo danh sách edges cho route
    path_coords = []
    for nid in path_nodes:
        if nid in nodes:
            lat, lon = nodes[nid]
            path_coords.append([lat, lon])

    path_edges = []
    for i in range(len(path_nodes)-1):
        u, v = path_nodes[i], path_nodes[i+1]
        lat1, lon1 = nodes[u]
        lat2, lon2 = nodes[v]
        traffic = "free"
        for e in graph[u]:
            if e["neighbor"] == v:
                traffic = e.get("traffic", "free")
                break
        path_edges.append({
            "coords": [[lat1, lon1], [lat2, lon2]],
            "traffic": traffic
        })

    return jsonify({
        "success": True,
        "path": path_coords,
        "edges": path_edges,
        "time_minutes": round(time_cost/60, 2),
        "distance_km": round(dist_cost/1000, 2)
    })

@app.route("/admin/reset", methods=["POST"])
def reset_graph():
    for u, neighbors in graph.items():
        for e in neighbors:
            e["traffic"] = "free"
    return jsonify({"success": True, "message": "Đã đặt lại trạng thái toàn bộ đường"})

# API trả về toàn bộ edges (cho admin)
@app.route("/edges")
def edges():
    edge_list = []
    for u, neighbors in graph.items():
        for e in neighbors:
            v = e["neighbor"]
            lat1, lon1 = nodes[u]
            lat2, lon2 = nodes[v]
            edge_list.append({
                "u": u,
                "v": v,
                "coords": [[lat1, lon1], [lat2, lon2]],
                "status": e.get("traffic", "free")
            })
    return jsonify({"edges": edge_list})

# API tìm node gần nhất (cho admin click)
@app.route("/nearest_node")
def nearest_node():
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    nid = str(ox.distance.nearest_nodes(G, lng, lat))
    return jsonify({"node": nid})

# API admin cập nhật trạng thái 1 cạnh
@app.route("/admin/set_status", methods=["POST"])
def set_status():
    data = request.get_json()
    u, v, status = str(data.get("u")), str(data.get("v")), data.get("status")

    updated = False
    for node1, node2 in [(u, v), (v, u)]:
        if node1 in graph:
            for edge in graph[node1]:
                if str(edge["neighbor"]) == node2:
                    edge["traffic"] = status
                    updated = True

    if updated:
        return jsonify({"success": True, "message": f"Đã cập nhật {status} cho cạnh {u}-{v}"})
    else:
        return jsonify({"success": False, "message": "Không tìm thấy cạnh"})

@app.route("/admin/set_path_status", methods=["POST"])
def set_path_status():
    data = request.get_json()
    start = data.get("start")   # [lat, lng]
    goal = data.get("goal")     # [lat, lng]
    status = data.get("status", "blocked")  # admin chọn trạng thái

    if not (start and goal):
        return jsonify({"success": False, "message": "Thiếu điểm start hoặc goal"}), 400

    start_lat, start_lng = start
    goal_lat, goal_lng = goal

    start_node = str(ox.distance.nearest_nodes(G, start_lng, start_lat))
    goal_node  = str(ox.distance.nearest_nodes(G, goal_lng, goal_lat))

    # tìm đường bằng A*
    path_nodes, _, _, _ = a_star(graph, nodes, start_node, goal_node, "motorcycle")

    if not path_nodes:
        return jsonify({"success": False, "message": "Không tìm được đường"}), 404

    # cập nhật trạng thái cho toàn bộ edges trong tuyến
    updated_edges = []
    for i in range(len(path_nodes)-1):
        u, v = path_nodes[i], path_nodes[i+1]
        for e in graph[u]:
            if e["neighbor"] == v:
                e["traffic"] = status
                updated_edges.append((u, v))
        for e in graph[v]:  # chiều ngược lại
            if e["neighbor"] == u:
                e["traffic"] = status
                updated_edges.append((v, u))

    return jsonify({
        "success": True,
        "message": f"Đã cập nhật {status} cho {len(updated_edges)} cạnh trong tuyến đường",
        "updated_edges": updated_edges
    })

# =======================
if __name__ == "__main__":
    app.run(debug=True)

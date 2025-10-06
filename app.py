from flask import Flask, request, jsonify, render_template
import osmnx as ox
from graph_utils import load_data, build_graph  # dùng load_data/ build_graph của bạn
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
# --------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    start = payload.get("start")   # [lat, lng]
    goal = payload.get("goal")     # [lat, lng]
    mode = payload.get("mode", "motorcycle")

    if not (isinstance(start, (list, tuple)) and isinstance(goal, (list, tuple))):
        return jsonify({"success": False, "message": "Dữ liệu start/goal sai định dạng"}), 400

    start_lat, start_lng = float(start[0]), float(start[1])
    goal_lat, goal_lng = float(goal[0]), float(goal[1])

    start_node_id = ox.distance.nearest_nodes(G, start_lng, start_lat)
    goal_node_id  = ox.distance.nearest_nodes(G, goal_lng, goal_lat)

    start_node = str(start_node_id)
    goal_node  = str(goal_node_id)

    path_nodes, time_cost = a_star(graph, nodes, start_node, goal_node, mode)

    if not path_nodes:
        return jsonify({"success": False, "message": "Không tìm được đường", "path": [], "time_minutes": None})

    path_coords = []
    for nid in path_nodes:
        if nid in nodes:
            lat, lon = nodes[nid]
            path_coords.append([lat, lon])
        else:
            try:
                n = int(nid)
                if n in G.nodes:
                    data = G.nodes[n]
                    path_coords.append([data.get("y"), data.get("x")])
            except:
                pass

    return jsonify({
        "success": True,
        "path": path_coords,
        "time_minutes": round(time_cost/60, 2)
    })

if __name__ == "__main__":
    app.run(debug=True)

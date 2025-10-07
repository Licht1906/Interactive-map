let map = L.map("map").setView([21.0227, 105.8195], 16);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
}).addTo(map);

let markers = [];
let routeLine = null;

// Click để chọn điểm A, B
map.on('click', function (e) {
    if (markers.length >= 2) {
        markers.forEach(m => map.removeLayer(m));
        markers = [];
        if (routeLine) {
            map.removeLayer(routeLine);
            routeLine = null;
        }
    }
    let marker = L.marker(e.latlng).addTo(map);
    markers.push(marker);
});

// Gửi yêu cầu tìm đường
document.getElementById("routeBtn").addEventListener("click", function () {
    if (markers.length < 2) {
        alert("Hãy chọn 2 điểm A và B trên bản đồ!");
        return;
    }

    let start = markers[0].getLatLng();
    let goal = markers[1].getLatLng();
    let mode = document.getElementById("mode").value;

    fetch("/route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            start: [start.lat, start.lng],
            goal: [goal.lat, goal.lng],
            mode: mode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Xoá route cũ
            if (routeLine) {
                routeLine.forEach(l => map.removeLayer(l));
            }
            routeLine = [];

            // Vẽ từng cạnh theo traffic
            data.edges.forEach(edge => {
                let color = "green";
                if (edge.traffic === "medium") color = "yellow";
                else if (edge.traffic === "heavy") color = "orange";
                else if (edge.traffic === "blocked") color = "red";

                let poly = L.polyline(edge.coords, {color: color, weight: 6}).addTo(map);
                routeLine.push(poly);

                if (edge.traffic === "blocked") {
                    let midLat = (edge.coords[0][0] + edge.coords[1][0]) / 2;
                    let midLng = (edge.coords[0][1] + edge.coords[1][1]) / 2;
                    let banIcon = L.divIcon({
                        className: "ban-icon",
                        html: "🚫",
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    });
                    let marker = L.marker([midLat, midLng], {icon: banIcon}).addTo(map);
                    routeLine.push(marker);
                }
            });

            // Hiển thị thông tin
            document.getElementById("info").innerText =
                `Thời gian dự kiến: ${data.time_minutes} phút - Quãng đường: ${data.distance_km} km`;
        } else {
            alert("Không tìm được đường đi!");
        }
    });
});

document.getElementById("clearBtn").addEventListener("click", function () {
    // Xoá marker
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    // Xoá đường đi (nếu là array nhiều đoạn)
    if (routeLine) {
        if (Array.isArray(routeLine)) {
            routeLine.forEach(l => map.removeLayer(l));
        } else {
            map.removeLayer(routeLine);
        }
        routeLine = [];
    }

    // Xoá thông tin hiển thị
    document.getElementById("info").innerText = "";
});


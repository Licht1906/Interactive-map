let map = L.map('map').setView([21.021, 105.830], 16); // Hà Nội center

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
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
        if (data.path && data.path.length > 0) {
            let latlngs = data.path.map(p => [p[0], p[1]]);
            routeLine = L.polyline(latlngs, {color: 'blue'}).addTo(map);
            map.fitBounds(routeLine.getBounds());
        } else {
            alert("Không tìm được đường đi!");
        }
    });
});

document.getElementById("clearBtn").addEventListener("click", function () {
    // Xóa marker
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    // Xóa đường
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }
});

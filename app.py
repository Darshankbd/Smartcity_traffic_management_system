import os
import json
from flask import Flask, render_template_string, jsonify, request, send_from_directory
from db_setup_and_ingest import connect_mongodb, DATA_FILE, DB_NAME, COLLECTION_NAME
from queries_and_analytics import run_all_queries, haversine_distance

app = Flask(__name__)
VIS_DIR = "C:/Users/kbd05/.gemini/antigravity/scratch/smart_city_traffic/visualizations"

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart City IoT Traffic & Location Analytics | MongoDB BDA Project</title>
    
    <!-- Bootstrap 5 & FontAwesome -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <!-- Chart.js & ApexCharts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>

    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg-body: #090d16;
            --card-bg: rgba(30, 41, 59, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-cyan: #38bdf8;
            --accent-pink: #f43f5e;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-purple: #a855f7;
            --text-main: #f8fafc;
        }

        body {
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(244, 63, 94, 0.05) 0%, transparent 40%);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
        }

        .navbar-custom {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--card-border);
            padding: 14px 28px;
        }

        .brand-text {
            font-weight: 800;
            font-size: 1.2rem;
            background: linear-gradient(135deg, #38bdf8 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
        }

        .metric-value {
            font-size: 2.1rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }

        #leafletMap {
            height: 480px;
            width: 100%;
            border-radius: 14px;
            border: 1px solid var(--card-border);
        }

        .section-header {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
        }

        .section-header i { color: var(--accent-cyan); }

        .select-location-box {
            background: #1e293b;
            border: 2px solid var(--accent-cyan);
            color: #f8fafc;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        .table-custom {
            font-size: 0.85rem;
            color: #cbd5e1;
        }
        .table-custom th {
            background-color: #0f172a;
            color: #38bdf8;
            border-color: #334155;
        }
        .table-custom td {
            border-color: #1e293b;
        }
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <nav class="navbar navbar-custom mb-4">
        <div class="container-fluid">
            <div class="d-flex align-items-center gap-3">
                <div class="p-2 rounded-3 bg-primary bg-opacity-20 border border-primary border-opacity-30">
                    <i class="fa-solid fa-map-pin text-info fs-4"></i>
                </div>
                <div>
                    <div class="brand-text">SMART CITY TRAFFIC MONITORING & LOCATION INSPECTOR</div>
                    <div class="text-secondary small fw-semibold">MongoDB 2dsphere Location Querying • 15 City Intersections</div>
                </div>
            </div>
            <div class="d-flex align-items-center gap-3">
                <!-- Location Selector Widget -->
                <div class="d-flex align-items-center gap-2">
                    <i class="fa-solid fa-location-dot text-info fs-5"></i>
                    <select id="locationSelect" class="form-select select-location-box" onchange="onLocationChange()">
                        <option value="">-- Select Place / Intersection --</option>
                    </select>
                </div>
                <a href="/download_report" class="btn btn-outline-info btn-sm rounded-3 fw-bold px-3">
                    <i class="fa-solid fa-file-pdf me-1"></i> PDF Report
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4 pb-5">
        
        <!-- Place Inspection Header Banner (Visible when a location is selected) -->
        <div id="placeBanner" class="alert alert-info bg-dark text-light border-info d-flex justify-content-between align-items-center mb-4 rounded-4 shadow-lg p-3">
            <div>
                <h4 id="selectedPlaceTitle" class="mb-1 text-info fw-bold"><i class="fa-solid fa-building-flag me-2"></i> Silk Board Junction</h4>
                <div id="selectedPlaceCoords" class="text-secondary small">Coordinates: GeoJSON [77.6229, 12.9172] • 10 Installed IoT Sensors</div>
            </div>
            <div class="d-flex gap-3 text-center">
                <div class="px-3 border-end border-secondary">
                    <div class="text-secondary small">Avg Speed</div>
                    <div id="locSpeed" class="fw-bold text-success fs-4">52.5 km/h</div>
                </div>
                <div class="px-3 border-end border-secondary">
                    <div class="text-secondary small">Signal Delay</div>
                    <div id="locWait" class="fw-bold text-warning fs-4">120 sec</div>
                </div>
                <div class="px-3">
                    <div class="text-secondary small">Noise Level</div>
                    <div id="locNoise" class="fw-bold text-danger fs-4">78 dB</div>
                </div>
            </div>
        </div>

        <!-- Main Dashboard Grid -->
        <div class="row g-4 mb-4">
            
            <!-- Left Column: Map & Selected Location Details -->
            <div class="col-xl-7">
                <div class="glass-card mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="section-header mb-0">
                            <i class="fa-solid fa-map-location-dot"></i> Interactive Location Map & Hotspots
                        </div>
                        <span class="badge bg-primary">Click Any Marker to Inspect Place</span>
                    </div>
                    <div id="leafletMap"></div>
                </div>

                <!-- Selected Location Readings Table -->
                <div class="glass-card">
                    <div class="section-header">
                        <i class="fa-solid fa-table text-info"></i> MongoDB Readings at Selected Location
                    </div>
                    <div class="table-responsive" style="max-height: 250px;">
                        <table class="table table-dark table-striped table-custom">
                            <thead>
                                <tr>
                                    <th>Sensor ID</th>
                                    <th>Status</th>
                                    <th>Vehicle Count</th>
                                    <th>Avg Speed</th>
                                    <th>Signal Wait</th>
                                    <th>Noise (dB)</th>
                                </tr>
                            </thead>
                            <tbody id="readingsTableBody">
                                <tr><td colspan="6" class="text-center text-secondary">Select a place from the dropdown above to view MongoDB documents...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Right Column: Place Specific Analytics & Demographics -->
            <div class="col-xl-5">
                
                <!-- Chart 1: Vehicle Breakdown at Location -->
                <div class="glass-card mb-4">
                    <div class="section-header">
                        <i class="fa-solid fa-chart-pie text-info"></i> Vehicle Mix at Selected Location
                    </div>
                    <div id="locVehiclePie" style="min-height: 220px;"></div>
                </div>

                <!-- Chart 2: Commuter Demographics at Location -->
                <div class="glass-card mb-4">
                    <div class="section-header">
                        <i class="fa-solid fa-user-group text-warning"></i> Commuter Breakdown at Selected Location
                    </div>
                    <div style="height: 200px;">
                        <canvas id="locCommuterChart"></canvas>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <!-- Leaflet JS & Plugins -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

    <script>
        let map, heatLayer, markersGroup;
        let vehiclePieChart, commuterChart;

        document.addEventListener('DOMContentLoaded', () => {
            initMap();
            loadLocationsList();
        });

        function initMap() {
            map = L.map('leafletMap').setView([12.9650, 77.6150], 12);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);
            markersGroup = L.layerGroup().addTo(map);

            fetch('/api/map_points')
                .then(r => r.json())
                .then(data => {
                    const heatPoints = data.map(d => [d.lat, d.lon, d.weight]);
                    heatLayer = L.heatLayer(heatPoints, { radius: 22, blur: 14, maxZoom: 13 }).addTo(map);
                });
        }

        function loadLocationsList() {
            fetch('/api/locations_list')
                .then(r => r.json())
                .then(locs => {
                    const select = document.getElementById('locationSelect');
                    locs.forEach(loc => {
                        const opt = document.createElement('option');
                        opt.value = loc.name;
                        opt.innerText = loc.name;
                        select.appendChild(opt);

                        // Add Interactive Marker to Map
                        const marker = L.circleMarker([loc.coords[1], loc.coords[0]], {
                            radius: 9, color: '#38bdf8', fillColor: '#38bdf8', fillOpacity: 0.8
                        }).bindPopup(`<b>${loc.name}</b><br>Click to inspect traffic data`);
                        
                        marker.on('click', () => {
                            select.value = loc.name;
                            fetchLocationDetails(loc.name);
                        });

                        markersGroup.addLayer(marker);
                    });

                    // Select first place by default
                    if (locs.length > 0) {
                        select.value = locs[0].name;
                        fetchLocationDetails(locs[0].name);
                    }
                });
        }

        function onLocationChange() {
            const locName = document.getElementById('locationSelect').value;
            if (locName) fetchLocationDetails(locName);
        }

        function fetchLocationDetails(roadName) {
            fetch(`/api/location_details?road_name=${encodeURIComponent(roadName)}`)
                .then(r => r.json())
                .then(data => {
                    // Update Banner Header
                    document.getElementById('selectedPlaceTitle').innerText = data.road_name;
                    document.getElementById('selectedPlaceCoords').innerText = `GeoJSON Point [${data.coords[0]}, ${data.coords[1]}] • ${data.readings_count} Snapshots Analyzed`;
                    document.getElementById('locSpeed').innerText = `${data.avg_speed.toFixed(1)} km/h`;
                    document.getElementById('locWait').innerText = `${data.avg_wait.toFixed(0)} sec`;
                    document.getElementById('locNoise').innerText = `${data.avg_noise.toFixed(1)} dB`;

                    // Fly map to place
                    map.flyTo([data.coords[1], data.coords[0]], 14);

                    // Update Table
                    const tbody = document.getElementById('readingsTableBody');
                    tbody.innerHTML = '';
                    data.latest_readings.forEach(r => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><span class="badge bg-secondary">${r.sensor_id}</span></td>
                            <td><span class="badge ${r.status === 'Heavy Congestion' ? 'bg-danger' : (r.status === 'Moderate Traffic' ? 'bg-warning' : 'bg-success')}">${r.status}</span></td>
                            <td class="fw-bold">${r.vehicle_count}</td>
                            <td>${r.avg_speed} km/h</td>
                            <td>${r.signal_wait_time_sec}s</td>
                            <td>${r.noise_level_db} dB</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    // Update Charts
                    renderVehiclePie(data.vehicle_mix);
                    renderCommuterBar(data.commuters);
                });
        }

        function renderVehiclePie(vMix) {
            const options = {
                series: [vMix.two_wheelers, vMix.cars, vMix.auto_rickshaws, vMix.buses, vMix.trucks],
                labels: ['Two Wheelers', 'Cars', 'Auto Rickshaws', 'Buses', 'Trucks'],
                chart: { type: 'pie', height: 220 },
                colors: ['#38bdf8', '#818cf8', '#f59e0b', '#10b981', '#f43f5e'],
                legend: { position: 'bottom', labels: { colors: '#f8fafc' } }
            };
            if (vehiclePieChart) vehiclePieChart.destroy();
            vehiclePieChart = new ApexCharts(document.querySelector("#locVehiclePie"), options);
            vehiclePieChart.render();
        }

        function renderCommuterBar(commuters) {
            const ctx = document.getElementById('locCommuterChart').getContext('2d');
            if (commuterChart) commuterChart.destroy();
            commuterChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Office Workers', 'Students', 'Daily Commuters', 'Commercial Drivers'],
                    datasets: [{
                        label: 'Commuter Count',
                        data: [commuters.office_workers, commuters.students, commuters.daily_commuters, commuters.commercial_drivers],
                        backgroundColor: ['#a855f7', '#38bdf8', '#10b981', '#f59e0b'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/download_report')
def download_report():
    pdf_path = "C:/Users/kbd05/.gemini/antigravity/scratch/smart_city_traffic/Smart_City_Traffic_Monitoring_Project_Report.pdf"
    if os.path.exists(pdf_path):
        return send_from_directory(os.path.dirname(pdf_path), os.path.basename(pdf_path), as_attachment=True)
    return "Report not generated yet", 404

@app.route('/api/locations_list')
def api_locations_list():
    from generate_data import ROAD_NODES
    locs = [{"name": node["name"], "coords": node["base_coords"]} for node in ROAD_NODES]
    return jsonify(locs)

@app.route('/api/location_details')
def api_location_details():
    road_name = request.args.get('road_name', 'Silk Board Junction')
    client = connect_mongodb()
    
    if client:
        db = client[DB_NAME]
        col = db[COLLECTION_NAME]
        
        readings = list(col.find({"road_name": road_name}).limit(100))
        if not readings:
            return jsonify({"error": "Location not found"}), 404
            
        coords = readings[0]["location"]["coordinates"]
        avg_speed = sum(r["avg_speed"] for r in readings) / len(readings)
        avg_wait = sum(r.get("signal_wait_time_sec", 60) for r in readings) / len(readings)
        avg_noise = sum(r.get("noise_level_db", 70) for r in readings) / len(readings)
        
        v_tw = sum(r.get("vehicle_breakdown", {}).get("two_wheelers", 0) for r in readings)
        v_cars = sum(r.get("vehicle_breakdown", {}).get("cars", 0) for r in readings)
        v_auto = sum(r.get("vehicle_breakdown", {}).get("auto_rickshaws", 0) for r in readings)
        v_buses = sum(r.get("vehicle_breakdown", {}).get("buses", 0) for r in readings)
        v_trucks = sum(r.get("vehicle_breakdown", {}).get("trucks", 0) for r in readings)
        
        c_office = sum(r.get("commuter_demographics", {}).get("office_workers", 0) for r in readings)
        c_students = sum(r.get("commuter_demographics", {}).get("students", 0) for r in readings)
        c_daily = sum(r.get("commuter_demographics", {}).get("daily_commuters", 0) for r in readings)
        c_comm = sum(r.get("commuter_demographics", {}).get("commercial_drivers", 0) for r in readings)
        
        latest_readings = [{
            "sensor_id": r["sensor_id"],
            "status": r["status"],
            "vehicle_count": r["vehicle_count"],
            "avg_speed": r["avg_speed"],
            "signal_wait_time_sec": r.get("signal_wait_time_sec", 60),
            "noise_level_db": r.get("noise_level_db", 70)
        } for r in readings[:8]]
        
    else:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        readings = [d for d in raw_data if d["road_name"] == road_name]
        coords = readings[0]["location"]["coordinates"] if readings else [77.6229, 12.9172]
        avg_speed = sum(r["avg_speed"] for r in readings) / len(readings) if readings else 52.5
        avg_wait = sum(r.get("signal_wait_time_sec", 60) for r in readings) / len(readings) if readings else 90.0
        avg_noise = sum(r.get("noise_level_db", 70) for r in readings) / len(readings) if readings else 75.0
        
        v_tw = sum(r.get("vehicle_breakdown", {}).get("two_wheelers", 0) for r in readings)
        v_cars = sum(r.get("vehicle_breakdown", {}).get("cars", 0) for r in readings)
        v_auto = sum(r.get("vehicle_breakdown", {}).get("auto_rickshaws", 0) for r in readings)
        v_buses = sum(r.get("vehicle_breakdown", {}).get("buses", 0) for r in readings)
        v_trucks = sum(r.get("vehicle_breakdown", {}).get("trucks", 0) for r in readings)
        
        c_office = sum(r.get("commuter_demographics", {}).get("office_workers", 0) for r in readings)
        c_students = sum(r.get("commuter_demographics", {}).get("students", 0) for r in readings)
        c_daily = sum(r.get("commuter_demographics", {}).get("daily_commuters", 0) for r in readings)
        c_comm = sum(r.get("commuter_demographics", {}).get("commercial_drivers", 0) for r in readings)
        
        latest_readings = [{
            "sensor_id": r["sensor_id"],
            "status": r["status"],
            "vehicle_count": r["vehicle_count"],
            "avg_speed": r["avg_speed"],
            "signal_wait_time_sec": r.get("signal_wait_time_sec", 60),
            "noise_level_db": r.get("noise_level_db", 70)
        } for r in readings[:8]]
        
    return jsonify({
        "road_name": road_name,
        "coords": coords,
        "readings_count": len(readings),
        "avg_speed": avg_speed,
        "avg_wait": avg_wait,
        "avg_noise": avg_noise,
        "vehicle_mix": {
            "two_wheelers": v_tw, "cars": v_cars, "auto_rickshaws": v_auto, "buses": v_buses, "trucks": v_trucks
        },
        "commuters": {
            "office_workers": c_office, "students": c_students, "daily_commuters": c_daily, "commercial_drivers": c_comm
        },
        "latest_readings": latest_readings
    })

@app.route('/api/map_points')
def api_map_points():
    client = connect_mongodb()
    points = []
    if client:
        db = client[DB_NAME]
        col = db[COLLECTION_NAME]
        cursor = col.find({}, {"_id": 0, "location": 1, "road_name": 1, "vehicle_count": 1, "avg_speed": 1, "status": 1}).limit(2000)
        for d in cursor:
            coords = d["location"]["coordinates"]
            weight = float(d["vehicle_count"]) / max(1.0, float(d["avg_speed"]))
            points.append({"lat": coords[1], "lon": coords[0], "weight": min(1.0, weight / 5.0)})
    else:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        for d in raw_data[:2000]:
            coords = d["location"]["coordinates"]
            weight = float(d["vehicle_count"]) / max(1.0, float(d["avg_speed"]))
            points.append({"lat": coords[1], "lon": coords[0], "weight": min(1.0, weight / 5.0)})
    return jsonify(points)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

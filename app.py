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
    <title>Smart City IoT Traffic & Time Interval Analytics | MongoDB BDA Project</title>
    
    <!-- Bootstrap 5 & FontAwesome -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    
    <!-- Leaflet CSS -->
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
        }

        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
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

        .time-tab-btn {
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 0.82rem;
            font-weight: 700;
            transition: all 0.2s;
        }
        .time-tab-btn.active, .time-tab-btn:hover {
            background: #2563eb;
            color: white;
            border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
        }

        .select-location-box {
            background: #1e293b;
            border: 2px solid var(--accent-cyan);
            color: #f8fafc;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 700;
        }
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <nav class="navbar navbar-custom mb-4">
        <div class="container-fluid">
            <div class="d-flex align-items-center gap-3">
                <div class="p-2 rounded-3 bg-primary bg-opacity-20 border border-primary border-opacity-30">
                    <i class="fa-solid fa-clock text-info fs-4"></i>
                </div>
                <div>
                    <div class="brand-text">SMART CITY TRAFFIC TIME INTERVAL ANALYTICS</div>
                    <div class="text-secondary small fw-semibold">MongoDB 2dsphere Geospatial • Time Interval Window Analysis</div>
                </div>
            </div>
            <div class="d-flex align-items-center gap-3">
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
        
        <!-- Interactive Time Interval Window Tabs -->
        <div class="glass-card mb-4">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                <div class="section-header mb-0">
                    <i class="fa-solid fa-business-time text-warning"></i> Select Traffic Time Interval Window:
                </div>
                <div class="d-flex gap-2 flex-wrap">
                    <button class="time-tab-btn active" onclick="filterTimeInterval('all', this)">All Hours (24h)</button>
                    <button class="time-tab-btn" onclick="filterTimeInterval('morning_peak', this)">🚨 Morning Peak (08:00–11:00 AM)</button>
                    <button class="time-tab-btn" onclick="filterTimeInterval('midday', this)">🟡 Midday Moderate (11:00 AM–05:00 PM)</button>
                    <button class="time-tab-btn" onclick="filterTimeInterval('evening_peak', this)">🚨 Evening Peak (05:00–09:00 PM)</button>
                    <button class="time-tab-btn" onclick="filterTimeInterval('night_light', this)">🟢 Night Light Traffic (10:00 PM–06:00 AM)</button>
                </div>
            </div>
        </div>

        <!-- Main Content Row -->
        <div class="row g-4 mb-4">
            
            <!-- Left Column: Time Interval Graphical Analytics & Map -->
            <div class="col-xl-7">
                
                <!-- NEW FEATURE: Time Interval Graphical Comparison Chart -->
                <div class="glass-card mb-4">
                    <div class="section-header">
                        <i class="fa-solid fa-chart-line text-info"></i> Traffic Intensity & Speed by Time Intervals
                    </div>
                    <div style="height: 250px;">
                        <canvas id="timeIntervalGraphChart"></canvas>
                    </div>
                </div>

                <div class="glass-card">
                    <div class="section-header mb-3">
                        <i class="fa-solid fa-map-location-dot"></i> Interactive Heatmap & Congestion Map
                    </div>
                    <div id="leafletMap"></div>
                </div>
            </div>

            <!-- Right Column: Time Slot Breakdown & Place Details -->
            <div class="col-xl-5">
                
                <!-- Time Interval Summary Card -->
                <div class="glass-card mb-4">
                    <div class="section-header">
                        <i class="fa-solid fa-list-check text-warning"></i> Active Time Window Metrics
                    </div>
                    <div class="row g-2 text-center">
                        <div class="col-6">
                            <div class="p-3 bg-dark rounded-3 border border-secondary">
                                <div class="text-secondary small">Traffic Intensity</div>
                                <div id="intervalStatus" class="fw-bold text-danger fs-5">Peak Rush</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-3 bg-dark rounded-3 border border-secondary">
                                <div class="text-secondary small">Avg Vehicle Volume</div>
                                <div id="intervalVolume" class="fw-bold text-info fs-5">50,800 / hr</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-3 bg-dark rounded-3 border border-secondary">
                                <div class="text-secondary small">Avg Travel Speed</div>
                                <div id="intervalSpeed" class="fw-bold text-success fs-5">45.8 km/h</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-3 bg-dark rounded-3 border border-secondary">
                                <div class="text-secondary small">Avg Signal Standing Delay</div>
                                <div id="intervalWait" class="fw-bold text-warning fs-5">190 sec</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 24-Hour Curve Chart -->
                <div class="glass-card mb-4">
                    <div class="section-header">
                        <i class="fa-solid fa-chart-area text-purple"></i> 24-Hour Bimodal Peak Curve
                    </div>
                    <div style="height: 210px;">
                        <canvas id="hourly24hChart"></canvas>
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
        let timeIntervalGraphChart, hourly24hChart;

        document.addEventListener('DOMContentLoaded', () => {
            initMap();
            loadLocationsList();
            loadTimeIntervalGraph();
            load24hHourlyChart();
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
                    });
                });
        }

        function onLocationChange() {
            const locName = document.getElementById('locationSelect').value;
            if (locName) {
                fetch('/api/locations_list')
                    .then(r => r.json())
                    .then(locs => {
                        const target = locs.find(l => l.name === locName);
                        if (target) map.flyTo([target.coords[1], target.coords[0]], 14);
                    });
            }
        }

        function loadTimeIntervalGraph() {
            fetch('/api/time_interval_stats')
                .then(r => r.json())
                .then(intervals => {
                    const labels = intervals.map(i => i.label);
                    const volumes = intervals.map(i => i.avg_hourly_volume);
                    const speeds = intervals.map(i => i.avg_speed);
                    const waits = intervals.map(i => i.avg_wait_sec);

                    const ctx = document.getElementById('timeIntervalGraphChart').getContext('2d');
                    timeIntervalGraphChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Hourly Vehicle Volume',
                                    data: volumes,
                                    backgroundColor: ['#f43f5e', '#f59e0b', '#f43f5e', '#10b981'],
                                    borderRadius: 6,
                                    yAxisID: 'y'
                                },
                                {
                                    label: 'Avg Speed (km/h)',
                                    data: speeds,
                                    type: 'line',
                                    borderColor: '#38bdf8',
                                    borderWidth: 3,
                                    yAxisID: 'y1'
                                },
                                {
                                    label: 'Signal Delay (sec)',
                                    data: waits,
                                    type: 'line',
                                    borderColor: '#a855f7',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    yAxisID: 'y1'
                                }
                            ]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            scales: {
                                x: { grid: { display: false }, ticks: { color: '#f8fafc', font: { size: 10, weight: 'bold' } } },
                                y: { position: 'left', grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                                y1: { position: 'right', grid: { display: false }, ticks: { color: '#38bdf8' } }
                            },
                            plugins: { legend: { labels: { color: '#f8fafc' } } }
                        }
                    });
                });
        }

        function filterTimeInterval(slotKey, btnElement) {
            document.querySelectorAll('.time-tab-btn').forEach(b => b.classList.remove('active'));
            btnElement.classList.add('active');

            fetch(`/api/time_interval_stats?slot=${slotKey}`)
                .then(r => r.json())
                .then(data => {
                    if (data.single) {
                        document.getElementById('intervalStatus').innerText = data.single.status;
                        document.getElementById('intervalVolume').innerText = `${data.single.avg_hourly_volume.toLocaleString()} / hr`;
                        document.getElementById('intervalSpeed').innerText = `${data.single.avg_speed.toFixed(1)} km/h`;
                        document.getElementById('intervalWait').innerText = `${data.single.avg_wait_sec.toFixed(0)} sec`;
                    }
                });
        }

        function load24hHourlyChart() {
            fetch('/api/analytics')
                .then(r => r.json())
                .then(data => {
                    const hours = data.q2_peak_hours.map(d => `${d._id}:00`);
                    const vehicles = data.q2_peak_hours.map(d => d.total_vehicles);

                    const ctx = document.getElementById('hourly24hChart').getContext('2d');
                    hourly24hChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: hours,
                            datasets: [{
                                label: '24h Total Vehicle Spikes',
                                data: vehicles,
                                borderColor: '#a855f7',
                                backgroundColor: 'rgba(168, 85, 247, 0.15)',
                                fill: true,
                                tension: 0.4
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

@app.route('/api/time_interval_stats')
def api_time_interval_stats():
    slot = request.args.get('slot', 'all')
    intervals = [
        {"slot": "morning_peak", "label": "Morning Peak (08-11 AM)", "status": "🚨 Severe Peak", "avg_hourly_volume": 50100, "avg_speed": 46.1, "avg_wait_sec": 185},
        {"slot": "midday", "label": "Midday Moderate (11 AM-05 PM)", "status": "🟡 Moderate", "avg_hourly_volume": 30200, "avg_speed": 57.3, "avg_wait_sec": 65},
        {"slot": "evening_peak", "label": "Evening Peak (05-09 PM)", "status": "🚨 Severe Peak", "avg_hourly_volume": 50800, "avg_speed": 45.8, "avg_wait_sec": 195},
        {"slot": "night_light", "label": "Night Light (10 PM-06 AM)", "status": "🟢 Smooth Flow", "avg_hourly_volume": 8200, "avg_speed": 58.6, "avg_wait_sec": 15}
    ]
    
    if slot != 'all':
        selected = next((i for i in intervals if i["slot"] == slot), intervals[0])
        return jsonify({"single": selected})
        
    return jsonify(intervals)

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

@app.route('/api/analytics')
def api_analytics():
    from queries_and_analytics import run_all_queries
    res = run_all_queries()
    return jsonify({
        "q2_peak_hours": res["q2_peak_hours"],
        "q3_lowest_speed": res["q3_lowest_speed"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

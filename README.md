# Smart City Traffic & Environmental Monitoring System (MongoDB & BDA 7th Sem Project)

A complete Big Data Analytics (BDA) application built using **MongoDB**, **Python**, **Folium**, **Matplotlib**, and **Flask** to ingest, index, and analyze real-time IoT sensor readings from traffic cameras and road sensors across urban corridors.

---

## 🌐 Live Web App & Cloud Links
- 🚀 **Render Live Cloud Demo:** **[https://smartcity-traffic-management-system.onrender.com](https://smartcity-traffic-management-system.onrender.com)**
- 💻 **Localhost Dashboard URL:** **[http://localhost:5000](http://localhost:5000)** (or `http://127.0.0.1:5000`)
- 🍃 **MongoDB Service URI:** **`mongodb://localhost:27017`**
- 📄 **Project Report Download:** **`http://localhost:5000/download_report`**

---

## 📌 Project Overview
- **Database:** MongoDB 7.0 (with `2dsphere` geospatial indexing)
- **Dataset:** 22,000+ IoT Sensor Documents (GeoJSON coordinates, vehicle category breakdown, commuter demographics, signal standing wait time, noise pollution dB, timestamps)
- **Analytics:** 7 Geospatial and Time-Series Aggregation Pipelines
- **Visualizations:** Interactive Folium Heatmaps (`.html`) & Matplotlib Charts (`.png`)
- **Web Dashboard:** Interactive Flask Application (`http://localhost:5000` & Render Cloud)
- **Location Inspector:** Select from 15 major city intersections to view place-specific traffic statistics
- **Project Report:** Automated PDF Report Generation (`Smart_City_Traffic_Monitoring_Project_Report.pdf`)

---

## 📁 Repository Structure
```
Smartcity_traffic_management_system/
├── generate_data.py            # Generates 22,000+ synthetic IoT traffic sensor readings
├── db_setup_and_ingest.py      # Connects to MongoDB, creates 2dsphere index, bulk inserts data
├── queries_and_analytics.py    # Executes 7 complex geospatial & time-series MongoDB queries
├── generate_visualizations.py  # Builds Folium heatmap HTML and Matplotlib charts
├── generate_report.py          # Compiles publication-ready PDF project report
├── app.py                      # Interactive Web Dashboard (Flask) running at http://localhost:5000
├── run_all.py                  # 1-Click Automated Master Pipeline Runner
├── run_all.bat                 # 1-Click Windows Batch Runner
├── Procfile                    # Render Cloud Hosting Configuration
├── Dockerfile                  # Containerized deployment config
├── requirements.txt            # Dependencies
└── visualizations/             # Generated charts & map assets
```

---

## ⚡ Quick Execution Guide

### 1. Automate Everything (1-Click Run)
```bash
python run_all.py
```
*(Or double-click `run_all.bat` on Windows)*

---

### 2. Manual Step-by-Step Execution Guide

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Generate IoT Dataset (22,000+ Records)
```bash
python generate_data.py
```

#### Step 3: Ingest into MongoDB & Build `2dsphere` Index
Ensure MongoDB is running locally at `mongodb://localhost:27017`:
```bash
python db_setup_and_ingest.py
```

#### Step 4: Execute MongoDB Queries & Aggregations
```bash
python queries_and_analytics.py
```

#### Step 5: Generate Maps, Visual Charts & PDF Report
```bash
python generate_visualizations.py
python generate_report.py
```

#### Step 6: Launch Interactive Web Dashboard
```bash
python app.py
```
Open your browser at **[http://localhost:5000](http://localhost:5000)** or access the live cloud version at **[https://smartcity-traffic-management-system.onrender.com](https://smartcity-traffic-management-system.onrender.com)**!

---

## 🌐 Deploying to Render (Free Cloud Hosting)

1. Go to **[render.com](https://render.com)** and sign in with GitHub.
2. Click **New +** → **Web Service** → Select repository `Smartcity_traffic_management_system`.
3. Set **Build Command**: `pip install -r requirements.txt && python generate_data.py && python generate_visualizations.py && python generate_report.py`
4. Set **Start Command**: `gunicorn app:app`
5. Click **Create Web Service**!

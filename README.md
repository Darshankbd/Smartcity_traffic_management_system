# Smart City Traffic Monitoring System (MongoDB & BDA 7th Sem Project)

A complete Big Data Analytics (BDA) application built using **MongoDB**, **Python**, **Folium**, **Matplotlib**, and **Flask** to ingest, index, and analyze real-time IoT sensor readings from traffic cameras across urban corridors.

---

## 📌 Project Overview
- **Database:** MongoDB 7.0 (with `2dsphere` geospatial indexing)
- **Dataset:** 22,000+ IoT Sensor Documents (GeoJSON coordinates, vehicle count, speed, timestamps)
- **Analytics:** 5 Geospatial and Time-Series Aggregation Pipelines
- **Visualizations:** Interactive Folium Heatmaps (`.html`) & Matplotlib Charts (`.png`)
- **Web Dashboard:** Interactive Flask Application (`http://localhost:5000`)
- **Project Report:** Automated PDF Report Generation (`Smart_City_Traffic_Monitoring_Project_Report.pdf`)

---

## 📁 Repository Structure
```
smart_city_traffic/
├── generate_data.py            # Generates 22,000+ synthetic IoT traffic sensor readings
├── db_setup_and_ingest.py      # Connects to MongoDB, creates 2dsphere index, bulk inserts data
├── queries_and_analytics.py    # Executes 5 complex geospatial & time-series MongoDB queries
├── generate_visualizations.py  # Builds Folium heatmap HTML and Matplotlib charts
├── generate_report.py          # Compiles publication-ready PDF project report
├── app.py                      # Interactive Web Dashboard (Flask)
├── requirements.txt            # Dependencies
└── visualizations/             # Generated charts & map assets
```

---

## ⚡ Quick Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate IoT Dataset (22,000+ Records)
```bash
python generate_data.py
```

### 3. Ingest into MongoDB & Build `2dsphere` Index
Ensure MongoDB is running locally at `mongodb://localhost:27017` (or set `MONGO_URI` environment variable):
```bash
python db_setup_and_ingest.py
```

### 4. Execute MongoDB Queries & Aggregations
```bash
python queries_and_analytics.py
```

### 5. Generate Maps, Visual Charts & PDF Report
```bash
python generate_visualizations.py
python generate_report.py
```

### 6. Launch Interactive Web Dashboard
```bash
python app.py
```
Open your browser at `http://localhost:5000` to interact with the live map, radius search widget, and query engine!

---

## 🔍 Key MongoDB Queries Included

1. **Geospatial Proximity Search (`$near` with `2dsphere`)**:
   Finds sensors within 2.5 km of Silk Board Junction (`[77.6229, 12.9172]`).
2. **Peak Congestion Hours Aggregation (`$hour`)**:
   Groups vehicle counts by hour of the day to identify morning (8-10 AM) and evening (5-8 PM) traffic rush hours.
3. **Roads with Lowest Average Speed**:
   Identifies the top 10 bottleneck intersections across the city.
4. **Daily Vehicle Count Trend (`$dateToString`)**:
   Evaluates 30-day citywide vehicle volume trends.
5. **Severe Congestion Hotspot Classifier (`$match`)**:
   Filters for readings with speed < 15 km/h AND vehicle count > 110.

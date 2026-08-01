import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap, MarkerCluster
from queries_and_analytics import run_all_queries
from db_setup_and_ingest import DATA_FILE

OUTPUT_DIR = "C:/Users/kbd05/.gemini/antigravity/scratch/smart_city_traffic/visualizations"

def create_visualizations():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n=======================================================")
    print("      GENERATING EXTENDED TRAFFIC & POLLUTION CHARTS   ")
    print("=======================================================\n")
    
    query_results = run_all_queries()
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # ----------------------------------------------------
    # CHART 1: Peak Hour Traffic Bar Chart (Vehicle Count & Speed)
    # ----------------------------------------------------
    q2_data = query_results["q2_peak_hours"]
    hours = [r["_id"] for r in q2_data]
    total_vehicles = [r["total_vehicles"] for r in q2_data]
    avg_speeds = [r["avg_speed_kmh"] for r in q2_data]
    
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    color = '#1f77b4'
    ax1.set_xlabel('Hour of Day (24-Hour Format)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Total Vehicle Count', color=color, fontsize=11, fontweight='bold')
    bars = ax1.bar(hours, total_vehicles, color=sns.color_palette("mako", 24), alpha=0.85, edgecolor='black')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(range(0, 24))
    
    for i, bar in enumerate(bars):
        if hours[i] in [8, 9, 10, 17, 18, 19]:
            bar.set_color('#d9534f')
            
    ax2 = ax1.twinx()
    color = '#2ca02c'
    ax2.set_ylabel('Average Speed (km/h)', color=color, fontsize=11, fontweight='bold')
    ax2.plot(hours, avg_speeds, color=color, linewidth=2.5, marker='o', label='Avg Speed')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Hourly Traffic Volume & Speed Spikes (Red = Morning & Evening Peak)', fontsize=13, fontweight='bold')
    fig.tight_layout()
    chart1_path = os.path.join(OUTPUT_DIR, "peak_hours_chart.png")
    plt.savefig(chart1_path, dpi=300)
    plt.close()

    # ----------------------------------------------------
    # CHART 2: Lowest Avg Speed Roads (Bottlenecks)
    # ----------------------------------------------------
    q3_data = query_results["q3_lowest_speed"]
    road_names = [r["_id"] for r in q3_data]
    speeds = [r["avg_speed"] for r in q3_data]
    
    plt.figure(figsize=(10, 5.5))
    y_pos = range(len(road_names))
    bars = plt.barh(y_pos, speeds, color=sns.color_palette("flare", len(speeds)), edgecolor='black', alpha=0.9)
    plt.yticks(y_pos, road_names, fontsize=9.5, fontweight='bold')
    plt.xlabel('Average Speed (km/h)', fontsize=11, fontweight='bold')
    plt.title('Top 10 Bottleneck Corridors (Lowest Avg Speed)', fontsize=13, fontweight='bold')
    plt.gca().invert_yaxis()
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.1f} km/h', va='center', fontsize=9.5, fontweight='bold')
                 
    plt.xlim(0, max(speeds) + 10)
    plt.tight_layout()
    chart2_path = os.path.join(OUTPUT_DIR, "lowest_speed_bottlenecks.png")
    plt.savefig(chart2_path, dpi=300)
    plt.close()

    # ----------------------------------------------------
    # CHART 3: Vehicle Type Breakdown (Pie / Donut Chart)
    # ----------------------------------------------------
    q6_data = query_results.get("q6_vehicle_breakdown", {})
    v_labels = ['Two Wheelers', 'Cars', 'Auto Rickshaws', 'Buses', 'Trucks']
    v_counts = [
        q6_data.get('total_two_wheelers', 100),
        q6_data.get('total_cars', 80),
        q6_data.get('total_auto_rickshaws', 40),
        q6_data.get('total_buses', 15),
        q6_data.get('total_trucks', 10)
    ]
    
    plt.figure(figsize=(8, 6))
    colors_pie = ['#38bdf8', '#818cf8', '#f59e0b', '#10b981', '#f43f5e']
    plt.pie(v_counts, labels=v_labels, autopct='%1.1f%%', startangle=140, colors=colors_pie,
            textprops={'fontsize': 11, 'weight': 'bold'}, wedgeprops={'edgecolor': 'black', 'linewidth': 1.2})
    plt.title('Citywide Vehicle Class Distribution (% Composition)', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    chart3_path = os.path.join(OUTPUT_DIR, "vehicle_type_breakdown.png")
    plt.savefig(chart3_path, dpi=300)
    plt.close()

    # ----------------------------------------------------
    # CHART 4: Signal Wait Time vs Noise Level Correlation
    # ----------------------------------------------------
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    sample_data = raw_data[::20] # Subsample for clear scatter plot
    wait_times = [d.get("signal_wait_time_sec", 60) for d in sample_data]
    noise_levels = [d.get("noise_level_db", 70) for d in sample_data]
    statuses = [d.get("status", "Moderate") for d in sample_data]
    
    plt.figure(figsize=(9, 5.5))
    color_map = {"Heavy Congestion": "#f43f5e", "Moderate Traffic": "#f59e0b", "Smooth Flow": "#10b981"}
    point_colors = [color_map.get(s, "#38bdf8") for s in statuses]
    
    plt.scatter(wait_times, noise_levels, c=point_colors, alpha=0.7, edgecolors='black', linewidth=0.5, s=45)
    plt.xlabel('Traffic Light Signal Delay / Standing Time (seconds)', fontsize=11, fontweight='bold')
    plt.ylabel('Recorded Noise Level (dB)', fontsize=11, fontweight='bold')
    plt.title('Signal Waiting Time vs Noise Pollution Level (dB)', fontsize=13, fontweight='bold')
    
    # Custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Heavy Congestion', markerfacecolor='#f43f5e', markersize=8),
        Line2D([0], [0], marker='o', color='w', label='Moderate Traffic', markerfacecolor='#f59e0b', markersize=8),
        Line2D([0], [0], marker='o', color='w', label='Smooth Flow', markerfacecolor='#10b981', markersize=8)
    ]
    plt.legend(handles=legend_elements, loc='upper left', frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    chart4_path = os.path.join(OUTPUT_DIR, "noise_vs_wait_scatter.png")
    plt.savefig(chart4_path, dpi=300)
    plt.close()

    # ----------------------------------------------------
    # MAP: Folium Interactive Map
    # ----------------------------------------------------
    city_center = [12.9650, 77.6150]
    m = folium.Map(location=city_center, zoom_start=12, tiles="CartoDB dark_matter")
    heat_data = [[doc["location"]["coordinates"][1], doc["location"]["coordinates"][0], doc["vehicle_count"]/max(1.0, doc["avg_speed"])] for doc in raw_data[:5000]]
    HeatMap(heat_data, radius=18, blur=12, max_zoom=13).add_to(m)
    
    marker_cluster = MarkerCluster(name="Severe Hotspots").add_to(m)
    for h in query_results["q5_severe_hotspots"]:
        coords = h["sample_coords"]
        folium.Marker(
            location=[coords[1], coords[0]],
            popup=f"<b>{h['_id']}</b><br>Incidents: {h['severe_incidents']}<br>Min Speed: {h['min_speed']:.1f} km/h<br>Max Queue: {h['max_vehicles']} vehicles",
            tooltip=f"HOTSPOT: {h['_id']}",
            icon=folium.Icon(color='red', icon='warning-sign')
        ).add_to(marker_cluster)
        
    html_map_path = os.path.join(OUTPUT_DIR, "traffic_heatmap.html")
    m.save(html_map_path)
    
    print("Extended visualizations generated successfully.")
    return {
        "peak_hours_chart": chart1_path,
        "lowest_speed_bottlenecks": chart2_path,
        "vehicle_type_breakdown": chart3_path,
        "noise_vs_wait_scatter": chart4_path,
        "heatmap_html": html_map_path
    }

if __name__ == "__main__":
    create_visualizations()

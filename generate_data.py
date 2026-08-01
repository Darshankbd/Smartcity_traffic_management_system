import json
import random
import os
from datetime import datetime, timedelta

# Realistic road nodes and GPS coordinates (Bengaluru Urban Corridors)
ROAD_NODES = [
    {"name": "Silk Board Junction", "base_coords": [77.6229, 12.9172], "base_congestion": 0.85, "primary_commuters": ["office_workers", "daily_commuters"]},
    {"name": "Outer Ring Road - Marathahalli", "base_coords": [77.6984, 12.9569], "base_congestion": 0.80, "primary_commuters": ["office_workers", "daily_commuters"]},
    {"name": "Electronic City Flyover", "base_coords": [77.6648, 12.8452], "base_congestion": 0.65, "primary_commuters": ["office_workers"]},
    {"name": "MG Road Metro Station", "base_coords": [77.6070, 12.9756], "base_congestion": 0.60, "primary_commuters": ["daily_commuters", "students"]},
    {"name": "Hebbal Flyover Junction", "base_coords": [77.5920, 13.0358], "base_congestion": 0.75, "primary_commuters": ["daily_commuters", "commercial_drivers"]},
    {"name": "Indiranagar 100ft Road", "base_coords": [77.6412, 12.9784], "base_congestion": 0.55, "primary_commuters": ["students", "office_workers"]},
    {"name": "Koramangala Sony World Signal", "base_coords": [77.6271, 12.9352], "base_congestion": 0.70, "primary_commuters": ["students", "office_workers"]},
    {"name": "Whitefield ITPL Main Road", "base_coords": [77.7289, 12.9863], "base_congestion": 0.82, "primary_commuters": ["office_workers"]},
    {"name": "Bannerghatta Road - Dairy Circle", "base_coords": [77.5975, 12.9381], "base_congestion": 0.72, "primary_commuters": ["students", "daily_commuters"]},
    {"name": "Goraguntepalya Signal - Tumkur Rd", "base_coords": [77.5385, 13.0285], "base_congestion": 0.78, "primary_commuters": ["commercial_drivers", "daily_commuters"]},
    {"name": "Bellary Road - Mekhri Circle", "base_coords": [77.5855, 12.9982], "base_congestion": 0.68, "primary_commuters": ["office_workers", "daily_commuters"]},
    {"name": "Old Airport Road - Domlur", "base_coords": [77.6387, 12.9610], "base_congestion": 0.62, "primary_commuters": ["office_workers"]},
    {"name": "Richmond Road Flyover", "base_coords": [77.6011, 12.9602], "base_congestion": 0.50, "primary_commuters": ["students", "office_workers"]},
    {"name": "Jayanagar 4th Block Circle", "base_coords": [77.5828, 12.9293], "base_congestion": 0.45, "primary_commuters": ["daily_commuters", "students"]},
    {"name": "Yeshwanthpur Railway Station Rd", "base_coords": [77.5499, 13.0238], "base_congestion": 0.74, "primary_commuters": ["commercial_drivers", "daily_commuters"]}
]

SENSORS = []
sensor_counter = 101
for node in ROAD_NODES:
    for s_idx in range(10): # 10 sensors around each road node
        sensor_id = f"CAM_BLR_{sensor_counter}"
        sensor_counter += 1
        lon_jitter = random.uniform(-0.008, 0.008)
        lat_jitter = random.uniform(-0.008, 0.008)
        coords = [round(node["base_coords"][0] + lon_jitter, 6), round(node["base_coords"][1] + lat_jitter, 6)]
        SENSORS.append({
            "sensor_id": sensor_id,
            "road_name": node["name"],
            "base_coords": coords,
            "base_congestion": node["base_congestion"],
            "primary_commuters": node["primary_commuters"]
        })

def generate_traffic_data(num_records=22000, output_file="C:/Users/kbd05/.gemini/antigravity/scratch/smart_city_traffic/traffic_sensor_readings.json"):
    print(f"Generating {num_records} IoT traffic sensor reading documents with extended vehicle breakdown, commuter types & noise pollution...")
    readings = []
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_records):
        sensor = random.choice(SENSORS)
        random_minutes = random.randint(0, 30 * 24 * 60)
        reading_time = start_date + timedelta(minutes=random_minutes)
        hour = reading_time.hour
        is_weekend = reading_time.weekday() >= 5
        
        if not is_weekend and (8 <= hour <= 10 or 17 <= hour <= 20):
            peak_multiplier = random.uniform(1.6, 2.3)
        elif not is_weekend and (11 <= hour <= 16):
            peak_multiplier = random.uniform(0.9, 1.3)
        elif 22 <= hour or hour <= 5:
            peak_multiplier = random.uniform(0.15, 0.4)
        else:
            peak_multiplier = random.uniform(0.6, 1.0)
            
        base_count = int(random.gauss(50, 15) * sensor["base_congestion"] * peak_multiplier)
        vehicle_count = max(2, min(180, base_count))
        
        if vehicle_count > 120:
            avg_speed = round(random.uniform(4.5, 18.0), 2)
            status = "Heavy Congestion"
            signal_wait_time_sec = round(random.uniform(110.0, 240.0), 1) # 2 to 4 minutes signal delay
            noise_level_db = round(random.uniform(78.5, 96.0), 1)       # Loud honking & engine idling
            aqi_pm25 = int(random.gauss(240, 30))                       # Severe air quality drop
        elif vehicle_count > 60:
            avg_speed = round(random.uniform(18.5, 38.0), 2)
            status = "Moderate Traffic"
            signal_wait_time_sec = round(random.uniform(45.0, 105.0), 1)  # 1 to 1.5 minutes signal delay
            noise_level_db = round(random.uniform(66.0, 78.0), 1)
            aqi_pm25 = int(random.gauss(150, 25))
        else:
            avg_speed = round(random.uniform(38.5, 78.0), 2)
            status = "Smooth Flow"
            signal_wait_time_sec = round(random.uniform(10.0, 40.0), 1)   # Smooth green light flow
            noise_level_db = round(random.uniform(52.0, 65.5), 1)
            aqi_pm25 = int(random.gauss(75, 15))
            
        # Vehicle Breakdown Sub-document
        two_wheelers = int(vehicle_count * random.uniform(0.35, 0.50))
        cars = int(vehicle_count * random.uniform(0.25, 0.38))
        auto_rickshaws = int(vehicle_count * random.uniform(0.10, 0.20))
        buses = int(vehicle_count * random.uniform(0.04, 0.09))
        trucks = max(0, vehicle_count - (two_wheelers + cars + auto_rickshaws + buses))
        
        vehicle_breakdown = {
            "two_wheelers": two_wheelers,
            "cars": cars,
            "auto_rickshaws": auto_rickshaws,
            "buses": buses,
            "trucks": trucks
        }
        
        # Commuter Types Sub-document (Demographic Distribution)
        if "office_workers" in sensor["primary_commuters"] and (7 <= hour <= 10 or 17 <= hour <= 20):
            p_office = 0.55
            p_student = 0.15
        elif "students" in sensor["primary_commuters"] and (8 <= hour <= 16):
            p_office = 0.25
            p_student = 0.45
        else:
            p_office = 0.35
            p_student = 0.25
            
        office_workers = int(vehicle_count * p_office)
        students = int(vehicle_count * p_student)
        daily_commuters = int(vehicle_count * 0.20)
        commercial_drivers = max(0, vehicle_count - (office_workers + students + daily_commuters))
        
        commuter_demographics = {
            "office_workers": office_workers,
            "students": students,
            "daily_commuters": daily_commuters,
            "commercial_drivers": commercial_drivers
        }
        
        lon = round(sensor["base_coords"][0] + random.uniform(-0.0002, 0.0002), 6)
        lat = round(sensor["base_coords"][1] + random.uniform(-0.0002, 0.0002), 6)
        
        doc = {
            "reading_id": f"READ_{i+1:06d}",
            "sensor_id": sensor["sensor_id"],
            "road_name": sensor["road_name"],
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "vehicle_count": vehicle_count,
            "avg_speed": avg_speed,
            "signal_wait_time_sec": signal_wait_time_sec,
            "noise_level_db": noise_level_db,
            "aqi_pm25": aqi_pm25,
            "vehicle_breakdown": vehicle_breakdown,
            "commuter_demographics": commuter_demographics,
            "status": status,
            "timestamp": reading_time.isoformat()
        }
        readings.append(doc)
        
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(readings, f, indent=2)
        
    print(f"Successfully generated and saved {len(readings)} extended documents to '{output_file}'.")
    return readings

if __name__ == "__main__":
    generate_traffic_data(22000)

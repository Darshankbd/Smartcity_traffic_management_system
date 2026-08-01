import json
import math
from datetime import datetime
from db_setup_and_ingest import connect_mongodb, DATA_FILE, DB_NAME, COLLECTION_NAME

def haversine_distance(coord1, coord2):
    """Calculate distance in meters between two GeoJSON [lon, lat] points."""
    R = 6371000
    lon1, lat1 = math.radians(coord1[0]), math.radians(coord1[1])
    lon2, lat2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def run_all_queries():
    client = connect_mongodb()
    use_mongo = client is not None
    
    results = {}
    
    if use_mongo:
        db = client[DB_NAME]
        col = db[COLLECTION_NAME]
        print("\n=======================================================")
        print("  EXECUTING MONGODB GEOSPATIAL & EXTENDED BDA QUERIES  ")
        print("=======================================================\n")
        
        # ----------------------------------------------------
        # QUERY 1: Geospatial Proximity Search ($near with 2dsphere index)
        # ----------------------------------------------------
        target_coords = [77.6229, 12.9172]
        radius_meters = 2500
        q1_pipeline = col.find({
            "location": {
                "$near": {
                    "$geometry": { "type": "Point", "coordinates": target_coords },
                    "$maxDistance": radius_meters
                }
            }
        }).limit(5)
        
        results["q1_geospatial"] = [{
            "sensor_id": doc["sensor_id"],
            "road_name": doc["road_name"],
            "coords": doc["location"]["coordinates"],
            "vehicle_count": doc["vehicle_count"],
            "avg_speed": doc["avg_speed"],
            "status": doc["status"]
        } for doc in q1_pipeline]

        # ----------------------------------------------------
        # QUERY 2: Peak Congestion Hours (Grouping by $hour)
        # ----------------------------------------------------
        q2_pipeline = [
            {
                "$group": {
                    "_id": { "$hour": "$timestamp" },
                    "total_vehicles": { "$sum": "$vehicle_count" },
                    "avg_speed_kmh": { "$avg": "$avg_speed" },
                    "avg_wait_sec": { "$avg": "$signal_wait_time_sec" },
                    "avg_noise_db": { "$avg": "$noise_level_db" }
                }
            },
            { "$sort": { "_id": 1 } }
        ]
        results["q2_peak_hours"] = list(col.aggregate(q2_pipeline))

        # ----------------------------------------------------
        # QUERY 3: Roads with Lowest Average Speed (Bottlenecks)
        # ----------------------------------------------------
        q3_pipeline = [
            {
                "$group": {
                    "_id": "$road_name",
                    "avg_speed": { "$avg": "$avg_speed" },
                    "total_vehicles": { "$sum": "$vehicle_count" },
                    "avg_signal_delay_sec": { "$avg": "$signal_wait_time_sec" },
                    "avg_noise_db": { "$avg": "$noise_level_db" }
                }
            },
            { "$sort": { "avg_speed": 1 } },
            { "$limit": 10 }
        ]
        results["q3_lowest_speed"] = list(col.aggregate(q3_pipeline))

        # ----------------------------------------------------
        # QUERY 4: Daily Vehicle Count Trend
        # ----------------------------------------------------
        q4_pipeline = [
            {
                "$group": {
                    "_id": { "$dateToString": { "format": "%Y-%m-%d", "date": "$timestamp" } },
                    "daily_vehicles": { "$sum": "$vehicle_count" },
                    "avg_city_speed": { "$avg": "$avg_speed" }
                }
            },
            { "$sort": { "_id": 1 } }
        ]
        results["q4_daily_trend"] = list(col.aggregate(q4_pipeline))

        # ----------------------------------------------------
        # QUERY 5: Severe Congestion Hotspot Detector
        # ----------------------------------------------------
        q5_pipeline = [
            { "$match": { "avg_speed": { "$lt": 15.0 }, "vehicle_count": { "$gt": 110 } } },
            {
                "$group": {
                    "_id": "$road_name",
                    "severe_incidents": { "$sum": 1 },
                    "min_speed": { "$min": "$avg_speed" },
                    "max_vehicles": { "$max": "$vehicle_count" },
                    "max_signal_wait_sec": { "$max": "$signal_wait_time_sec" },
                    "sample_coords": { "$first": "$location.coordinates" }
                }
            },
            { "$sort": { "severe_incidents": -1 } }
        ]
        results["q5_severe_hotspots"] = list(col.aggregate(q5_pipeline))

        # ----------------------------------------------------
        # QUERY 6: Vehicle Class Distribution & Noise Pollution Aggregation
        # ----------------------------------------------------
        print("--- QUERY 6: City-Wide Vehicle Category Breakdown & Noise Levels ---")
        q6_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_two_wheelers": { "$sum": "$vehicle_breakdown.two_wheelers" },
                    "total_cars": { "$sum": "$vehicle_breakdown.cars" },
                    "total_auto_rickshaws": { "$sum": "$vehicle_breakdown.auto_rickshaws" },
                    "total_buses": { "$sum": "$vehicle_breakdown.buses" },
                    "total_trucks": { "$sum": "$vehicle_breakdown.trucks" },
                    "avg_noise_level_db": { "$avg": "$noise_level_db" },
                    "avg_aqi_pm25": { "$avg": "$aqi_pm25" }
                }
            }
        ]
        q6_res = list(col.aggregate(q6_pipeline))
        results["q6_vehicle_breakdown"] = q6_res[0] if q6_res else {}
        print(f" Vehicle Mix: Two Wheelers={results['q6_vehicle_breakdown'].get('total_two_wheelers', 0):,}, Cars={results['q6_vehicle_breakdown'].get('total_cars', 0):,}, Buses={results['q6_vehicle_breakdown'].get('total_buses', 0):,}")
        print(f" Citywide Avg Noise: {results['q6_vehicle_breakdown'].get('avg_noise_level_db', 0):.1f} dB | Avg AQI: {results['q6_vehicle_breakdown'].get('avg_aqi_pm25', 0):.0f}")

        # ----------------------------------------------------
        # QUERY 7: Commuter Impact & Signal Delay Analysis
        # ----------------------------------------------------
        print("\n--- QUERY 7: Commuter Impact (Office Workers vs Students) & Traffic Light Delay ---")
        q7_pipeline = [
            {
                "$group": {
                    "_id": "$road_name",
                    "avg_signal_wait_sec": { "$avg": "$signal_wait_time_sec" },
                    "office_workers_affected": { "$sum": "$commuter_demographics.office_workers" },
                    "students_affected": { "$sum": "$commuter_demographics.students" },
                    "daily_commuters_affected": { "$sum": "$commuter_demographics.daily_commuters" }
                }
            },
            { "$sort": { "avg_signal_wait_sec": -1 } },
            { "$limit": 10 }
        ]
        results["q7_commuter_impact"] = list(col.aggregate(q7_pipeline))
        for r in results["q7_commuter_impact"][:5]:
            print(f" Road: {r['_id']:<35} | Wait Time: {r['avg_signal_wait_sec']:.1f}s | Office Workers: {r['office_workers_affected']:,} | Students: {r['students_affected']:,}")
            
    else:
        # Fallback Python Simulation
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        target_coords = [77.6229, 12.9172]
        near_list = []
        for d in raw_data:
            dist = haversine_distance(target_coords, d["location"]["coordinates"])
            if dist <= 2500:
                near_list.append((dist, d))
        near_list.sort(key=lambda x: x[0])
        results["q1_geospatial"] = [{
            "sensor_id": d["sensor_id"],
            "road_name": d["road_name"],
            "coords": d["location"]["coordinates"],
            "vehicle_count": d["vehicle_count"],
            "avg_speed": d["avg_speed"],
            "status": d["status"]
        } for _, d in near_list[:5]]
        
        # Q2
        hourly = {}
        for d in raw_data:
            dt = datetime.fromisoformat(d["timestamp"])
            hr = dt.hour
            if hr not in hourly:
                hourly[hr] = {"total_vehicles": 0, "speeds": [], "waits": [], "noises": []}
            hourly[hr]["total_vehicles"] += d["vehicle_count"]
            hourly[hr]["speeds"].append(d["avg_speed"])
            hourly[hr]["waits"].append(d.get("signal_wait_time_sec", 60))
            hourly[hr]["noises"].append(d.get("noise_level_db", 70))
            
        results["q2_peak_hours"] = [
            {
                "_id": hr,
                "total_vehicles": hourly[hr]["total_vehicles"],
                "avg_speed_kmh": sum(hourly[hr]["speeds"]) / len(hourly[hr]["speeds"]),
                "avg_wait_sec": sum(hourly[hr]["waits"]) / len(hourly[hr]["waits"]),
                "avg_noise_db": sum(hourly[hr]["noises"]) / len(hourly[hr]["noises"])
            } for hr in sorted(hourly.keys())
        ]
        
        # Q3
        roads = {}
        for d in raw_data:
            rname = d["road_name"]
            if rname not in roads:
                roads[rname] = {"speeds": [], "vehicles": 0, "waits": [], "noises": []}
            roads[rname]["speeds"].append(d["avg_speed"])
            roads[rname]["vehicles"] += d["vehicle_count"]
            roads[rname]["waits"].append(d.get("signal_wait_time_sec", 60))
            roads[rname]["noises"].append(d.get("noise_level_db", 70))
                
        sorted_roads = sorted(roads.items(), key=lambda x: sum(x[1]["speeds"])/len(x[1]["speeds"]))
        results["q3_lowest_speed"] = [
            {
                "_id": rname,
                "avg_speed": sum(data["speeds"]) / len(data["speeds"]),
                "total_vehicles": data["vehicles"],
                "avg_signal_delay_sec": sum(data["waits"]) / len(data["waits"]),
                "avg_noise_db": sum(data["noises"]) / len(data["noises"])
            } for rname, data in sorted_roads[:10]
        ]
        
        # Q4
        daily = {}
        for d in raw_data:
            day_str = d["timestamp"][:10]
            if day_str not in daily:
                daily[day_str] = {"vehicles": 0, "speeds": []}
            daily[day_str]["vehicles"] += d["vehicle_count"]
            daily[day_str]["speeds"].append(d["avg_speed"])
            
        results["q4_daily_trend"] = [
            {
                "_id": dstr,
                "daily_vehicles": data["vehicles"],
                "avg_city_speed": sum(data["speeds"])/len(data["speeds"])
            } for dstr, data in sorted(daily.items())
        ]
        
        # Q5
        hotspots = {}
        for d in raw_data:
            if d["avg_speed"] < 15.0 and d["vehicle_count"] > 110:
                rname = d["road_name"]
                if rname not in hotspots:
                    hotspots[rname] = {
                        "incidents": 0, "min_speed": 999.0, "max_veh": 0, "coords": d["location"]["coordinates"]
                    }
                hotspots[rname]["incidents"] += 1
                hotspots[rname]["min_speed"] = min(hotspots[rname]["min_speed"], d["avg_speed"])
                hotspots[rname]["max_veh"] = max(hotspots[rname]["max_veh"], d["vehicle_count"])
                
        sorted_hotspots = sorted(hotspots.items(), key=lambda x: x[1]["incidents"], reverse=True)
        results["q5_severe_hotspots"] = [
            {
                "_id": rname,
                "severe_incidents": data["incidents"],
                "min_speed": data["min_speed"],
                "max_vehicles": data["max_veh"],
                "sample_coords": data["coords"]
            } for rname, data in sorted_hotspots
        ]
        
        # Q6
        v_tw = sum(d.get("vehicle_breakdown", {}).get("two_wheelers", 0) for d in raw_data)
        v_cars = sum(d.get("vehicle_breakdown", {}).get("cars", 0) for d in raw_data)
        v_auto = sum(d.get("vehicle_breakdown", {}).get("auto_rickshaws", 0) for d in raw_data)
        v_buses = sum(d.get("vehicle_breakdown", {}).get("buses", 0) for d in raw_data)
        v_trucks = sum(d.get("vehicle_breakdown", {}).get("trucks", 0) for d in raw_data)
        avg_n = sum(d.get("noise_level_db", 70) for d in raw_data) / len(raw_data)
        avg_a = sum(d.get("aqi_pm25", 150) for d in raw_data) / len(raw_data)
        
        results["q6_vehicle_breakdown"] = {
            "total_two_wheelers": v_tw,
            "total_cars": v_cars,
            "total_auto_rickshaws": v_auto,
            "total_buses": v_buses,
            "total_trucks": v_trucks,
            "avg_noise_level_db": avg_n,
            "avg_aqi_pm25": avg_a
        }
        
        # Q7
        c_impact = {}
        for d in raw_data:
            rname = d["road_name"]
            if rname not in c_impact:
                c_impact[rname] = {"waits": [], "office": 0, "students": 0, "daily": 0}
            c_impact[rname]["waits"].append(d.get("signal_wait_time_sec", 60))
            demo = d.get("commuter_demographics", {})
            c_impact[rname]["office"] += demo.get("office_workers", 0)
            c_impact[rname]["students"] += demo.get("students", 0)
            c_impact[rname]["daily"] += demo.get("daily_commuters", 0)
            
        sorted_impact = sorted(c_impact.items(), key=lambda x: sum(x[1]["waits"])/len(x[1]["waits"]), reverse=True)
        results["q7_commuter_impact"] = [
            {
                "_id": rname,
                "avg_signal_wait_sec": sum(data["waits"])/len(data["waits"]),
                "office_workers_affected": data["office"],
                "students_affected": data["students"],
                "daily_commuters_affected": data["daily"]
            } for rname, data in sorted_impact[:10]
        ]
        
    return results

if __name__ == "__main__":
    run_all_queries()

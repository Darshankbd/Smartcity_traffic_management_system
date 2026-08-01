import json
import os
from datetime import datetime
try:
    from pymongo import MongoClient, GEOSPHERE, ASCENDING, DESCENDING
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "smart_city_db"
COLLECTION_NAME = "traffic_readings"
DATA_FILE = "C:/Users/kbd05/.gemini/antigravity/scratch/smart_city_traffic/traffic_sensor_readings.json"

def connect_mongodb():
    if not PYMONGO_AVAILABLE:
        print("[WARNING] PyMongo is not installed.")
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print(f"[SUCCESS] Connected to MongoDB at {MONGO_URI}")
        return client
    except Exception as e:
        print(f"[NOTICE] MongoDB Server unavailable at {MONGO_URI} ({e}).")
        return None

def ingest_data():
    if not os.path.exists(DATA_FILE):
        print(f"Data file '{DATA_FILE}' not found. Running data generator first...")
        from generate_data import generate_traffic_data
        generate_traffic_data(22000, DATA_FILE)
        
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    print(f"Loaded {len(raw_data)} extended documents from dataset JSON.")
    
    processed_docs = []
    for doc in raw_data:
        doc_copy = dict(doc)
        if isinstance(doc_copy["timestamp"], str):
            doc_copy["timestamp"] = datetime.fromisoformat(doc_copy["timestamp"])
        processed_docs.append(doc_copy)
        
    client = connect_mongodb()
    if client:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        collection.drop()
        print(f"Dropped existing collection '{COLLECTION_NAME}'.")
        
        # 1. Geospatial 2dsphere Index
        collection.create_index([("location", GEOSPHERE)])
        print(" [INDEX CREATED] 2dsphere index created on 'location'.")
        
        # 2. Secondary & Compound Indexes
        collection.create_index([("timestamp", ASCENDING)])
        collection.create_index([("sensor_id", ASCENDING), ("timestamp", DESCENDING)])
        collection.create_index([("road_name", ASCENDING), ("signal_wait_time_sec", DESCENDING)])
        collection.create_index([("noise_level_db", DESCENDING), ("avg_speed", ASCENDING)])
        print(" [INDEX CREATED] Compound indexes created on signal_wait_time_sec and noise_level_db.")
        
        # 3. Bulk Insert
        result = collection.insert_many(processed_docs)
        print(f"[SUCCESS] Bulk inserted {len(result.inserted_ids)} extended sensor documents into MongoDB!")
        return True, collection
    else:
        print("[OFFLINE SIMULATION MODE] Ready with extended dataset.")
        return False, processed_docs

if __name__ == "__main__":
    ingest_data()

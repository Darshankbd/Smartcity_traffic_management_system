import os
import sys
import subprocess
import webbrowser
import time

def run_step(description, command):
    print(f"\n=======================================================")
    print(f"  STEP: {description}")
    print(f"=======================================================")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"[ERROR] {description} failed with return code {result.returncode}")
        sys.exit(result.returncode)
    print(f"[SUCCESS] {description} completed.")

def main():
    print("🚀 AUTOMATED PIPELINE: SMART CITY TRAFFIC MONITORING SYSTEM")
    
    # Step 1: Generate Data
    run_step("1/5 Generating 22,000+ IoT Sensor Documents", "python generate_data.py")
    
    # Step 2: MongoDB Ingestion & 2dsphere Indexing
    run_step("2/5 Ingesting Data to MongoDB & Building 2dsphere Index", "python db_setup_and_ingest.py")
    
    # Step 3: Run Queries
    run_step("3/5 Executing 7 MongoDB Geospatial & Aggregation Queries", "python queries_and_analytics.py")
    
    # Step 4: Visualizations & PDF Report
    run_step("4/5 Generating Folium Heatmap, Charts & PDF Report", "python generate_visualizations.py")
    run_step("4b/5 Compiling PDF Project Report", "python generate_report.py")
    
    # Step 5: Launch Web Dashboard & Open Browser
    print("\n=======================================================")
    print("  STEP 5/5: LAUNCHING INTERACTIVE WEB DASHBOARD")
    print("=======================================================")
    print("Opening browser at http://localhost:5000 ...")
    
    time.sleep(1)
    webbrowser.open("http://localhost:5000")
    
    # Start Flask App
    subprocess.run("python app.py", shell=True)

if __name__ == "__main__":
    main()

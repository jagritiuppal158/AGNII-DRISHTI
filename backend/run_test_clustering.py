import csv
import psycopg2
from pathlib import Path
from ingestion.firms_ingest import ingest
from config import settings

CSV_PATH = Path("data/test_clustering.csv")

def create_csv():
    # Matching the real VIIRS format
    headers = [
        "latitude","longitude","bright_ti4","scan","track","acq_date",
        "acq_time","satellite","instrument","confidence","version",
        "bright_ti5","frp","daynight"
    ]
    # 6 rows at the exact same coordinate (30.555, 77.555) over 6 hours
    rows = [
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1000", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1100", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1200", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1300", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1400", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
        [30.555, 77.555, 305.0, 0.4, 0.45, "2026-09-06", "1500", "N20", "VIIRS", "n", "2.0", 280, 1.5, "D"],
    ]
    
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Created {CSV_PATH}")

def run_test():
    create_csv()
    
    print("\nRunning ingestion script on test data...")
    ingest([CSV_PATH])
    
    print("\nQuerying locations table for the clustered point...")
    settings.require_supabase()
    conn = psycopg2.connect(settings.supabase_db_url)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, centroid_latitude, centroid_longitude, detection_count, status 
                FROM locations 
                WHERE centroid_latitude = 30.555 AND centroid_longitude = 77.555
            """)
            results = cur.fetchall()
            print("\n--- TEST RESULTS ---")
            for row in results:
                print(f"Location ID: {row[0]}")
                print(f"Centroid: {row[1]}, {row[2]}")
                print(f"Detection Count: {row[3]}")
                print(f"Status: {row[4]}")
                
                if row[3] >= 6 and row[4] == 'persistent':
                    print("\n✅ SUCCESS: detection_count hit 6 and status safely transitioned to 'persistent'!")
                else:
                    print("\n❌ FAILED: State transition did not work as expected.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_test()

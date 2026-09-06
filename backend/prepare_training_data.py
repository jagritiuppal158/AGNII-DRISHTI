import pandas as pd
import rasterio
import psycopg2
from pathlib import Path
from config import settings
from ingestion.firms_ingest import ingest
from routers.infra import get_nearest_infra
from routers.landcover import get_land_cover
from classification import classify_rule_based

def main():
    print("1. Reading pilot bounding box...")
    try:
        with rasterio.open("data/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif") as src:
            bounds = src.bounds
            min_lon, min_lat, max_lon, max_lat = bounds.left, bounds.bottom, bounds.right, bounds.top
        print(f"   Bounds: lat [{min_lat:.2f}, {max_lat:.2f}], lon [{min_lon:.2f}, {max_lon:.2f}]")
    except Exception as e:
        print("   Error reading TIFF, falling back to static bounds: ", e)
        # Fallback to rough bbox if TIF read fails
        min_lon, max_lon = 75.0, 78.0
        min_lat, max_lat = 27.0, 30.0

    print("\n2. Filtering national CSV to pilot region...")
    input_csv = Path("data/national_firms.csv")
    if not input_csv.exists():
        print("   ERROR: national_firms.csv not found. Did you run merge_firms.py?")
        return
        
    df = pd.read_csv(input_csv)
    initial_len = len(df)
    
    filtered_df = df[
        (df['latitude'] >= min_lat) & (df['latitude'] <= max_lat) &
        (df['longitude'] >= min_lon) & (df['longitude'] <= max_lon)
    ]
    print(f"   Filtered from {initial_len} down to {len(filtered_df)} hotspots.")
    
    filtered_csv = Path("data/pilot_firms.csv")
    filtered_df.to_csv(filtered_csv, index=False)
    
    print("\n3. Ingesting into database (clustering)...")
    ingest([filtered_csv])
    
    print("\n4. Applying weak supervision labels (rule-based)...")
    settings.require_supabase()
    conn = psycopg2.connect(settings.supabase_db_url)
    
    # We only process locations that don't have a label yet
    query = """
    SELECT id, centroid_latitude, centroid_longitude, detection_count, status
    FROM locations
    WHERE current_class IS NULL
    """
    
    update_query = """
    UPDATE locations 
    SET current_class = %(cls)s, current_confidence = %(conf)s
    WHERE id = %(id)s
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            locations = cur.fetchall()
            
            labeled = 0
            for loc in locations:
                loc_id, lat, lon, count, status = loc
                
                # Extract features for rule-based labelling
                infra_resp = get_nearest_infra(lat, lon)
                lc_resp = get_land_cover(lat, lon)
                
                features = {
                    "infra_type": infra_resp.infra_type,
                    "distance_to_infra": None if infra_resp.distance_meters == "none" else float(infra_resp.distance_meters),
                    "land_cover": lc_resp.get("land_cover", "unknown") if isinstance(lc_resp, dict) else lc_resp.land_cover,
                    "status": status,
                    "detection_count": count
                }
                
                result = classify_rule_based(features)
                
                # Skip locations where no rule matched — leave current_class as NULL
                # rather than inserting "unknown" which is not a valid enum value.
                if result["class"] == "unknown":
                    continue
                    
                cur.execute(update_query, {
                    "cls": result["class"],
                    "conf": result["confidence"],
                    "id": loc_id
                })
                labeled += 1
                
            conn.commit()
            print(f"   Assigned weak labels to {labeled} locations.")
            
        print("\n5. Distribution Check")
        # NOTE: These are weak supervision labels, explicitly assigned via the heuristic rule-based classifier!
        dist_query = "SELECT current_class, status FROM locations WHERE current_class IS NOT NULL"
        dist_df = pd.read_sql_query(dist_query, conn)
        
        print("\n--- CLASS DISTRIBUTION (Weak Supervision Labels) ---")
        print(dist_df['current_class'].value_counts())
        
        print("\n--- STATUS DISTRIBUTION ---")
        print(dist_df['status'].value_counts())
        
    finally:
        conn.close()
        
    print("\n*** STOPPING FOR REVIEW ***")
    print("Please review the distributions above. Do not proceed to train_model.py until you are satisfied with the class representation.")

if __name__ == "__main__":
    main()

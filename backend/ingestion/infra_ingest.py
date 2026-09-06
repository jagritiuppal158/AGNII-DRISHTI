"""
ingestion/infra_ingest.py — Load industrial geojson into infra_context
"""
import json
import logging
import sys
from pathlib import Path
import psycopg2
import psycopg2.extras
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger("infra_ingest")

_INSERT_SQL = """
INSERT INTO infra_context (infra_type, geom)
VALUES (
    %(infra_type)s,
    ST_SetSRID(ST_GeomFromGeoJSON(%(geom_json)s), 4326)
);
"""

def extract_infra_type(props: dict) -> str:
    """Extract a meaningful type string from OSM properties."""
    for key in ["industrial", "man_made", "pipeline", "power", "landuse"]:
        val = props.get(key)
        if val and val != "yes":
            return val
    return "industrial"

def ingest(geojson_path: Path):
    if not geojson_path.exists():
        log.error("File not found: %s", geojson_path)
        sys.exit(1)
        
    log.info("Loading GeoJSON from %s", geojson_path)
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        
    features = data.get("features", [])
    records = []
    
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        if not geom:
            continue
            
        infra_type = extract_infra_type(props)
        records.append({
            "infra_type": infra_type,
            "geom_json": json.dumps(geom)
        })
        
    if not records:
        log.info("No features found to insert.")
        return
        
    settings.require_supabase()
    log.info("Connecting to database...")
    
    conn = psycopg2.connect(settings.supabase_db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, _INSERT_SQL, records, page_size=500)
        log.info("Inserted %d features into infra_context.", len(records))
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.infra_ingest <path/to/osm_industrial.geojson>", file=sys.stderr)
        sys.exit(1)
    ingest(Path(sys.argv[1]))

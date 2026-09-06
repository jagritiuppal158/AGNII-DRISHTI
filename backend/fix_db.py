import psycopg2
import sys
from config import settings

sql = """
DROP TABLE IF EXISTS infra_context;

CREATE TABLE infra_context (
    id SERIAL PRIMARY KEY,
    infra_type VARCHAR(255) NOT NULL,
    geom GEOMETRY(Geometry, 4326) NOT NULL
);

CREATE INDEX idx_infra_context_geom 
    ON infra_context USING GIST (geom);
"""

def fix_db():
    settings.require_supabase()
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(settings.supabase_db_url)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("Success! The infra_context table and geom column have been created.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    fix_db()

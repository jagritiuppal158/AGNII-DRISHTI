"""
routers/infra.py — Infrastructure proximity queries
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Union
from pydantic import BaseModel
import psycopg2
from config import settings

router = APIRouter(prefix="/infra", tags=["infra"])

class NearestInfraResponse(BaseModel):
    distance_meters: Union[float, str]
    infra_type: Optional[str]

@router.get("/nearest", response_model=NearestInfraResponse)
def get_nearest_infra(lat: float, lon: float):
    if settings.supabase_db_url.startswith("postgresql://placeholder"):
        # Return fallback if no db configured
        return NearestInfraResponse(distance_meters="none", infra_type=None)
        
    query = """
    SELECT infra_type,
           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography) as dist_m
    FROM infra_context
    WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography, 5000)
    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
    LIMIT 1;
    """
    
    try:
        conn = psycopg2.connect(settings.supabase_db_url)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, {"lat": lat, "lon": lon})
                row = cur.fetchone()
                
        if row:
            return NearestInfraResponse(distance_meters=round(row[1], 2), infra_type=row[0])
        else:
            return NearestInfraResponse(distance_meters="none", infra_type=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

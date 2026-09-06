"""
routers/landcover.py — Land cover queries from GeoTIFF
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from pathlib import Path
import rasterio

router = APIRouter(prefix="/landcover", tags=["landcover"])

WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen"
}

# The TIF path is relative to the backend directory
TIF_PATH = Path("data/worldcover_clip.tif")

class LandCoverResponse(BaseModel):
    land_cover: str

@router.get("/nearest", response_model=LandCoverResponse)
def get_land_cover(lat: float, lon: float):
    if not TIF_PATH.exists():
        return LandCoverResponse(land_cover="unknown")
        
    try:
        with rasterio.open(TIF_PATH) as dataset:
            # Check if the point is inside the bounding box
            if (lon < dataset.bounds.left or lon > dataset.bounds.right or
                lat < dataset.bounds.bottom or lat > dataset.bounds.top):
                return LandCoverResponse(land_cover="unknown")
            
            # Get the pixel row and col for the given lat/lon
            row, col = dataset.index(lon, lat)
            
            # Read the value at the pixel (assuming 1 band)
            val = dataset.read(1, window=((row, row+1), (col, col+1)))
            
            if val.size == 0:
                return LandCoverResponse(land_cover="unknown")
                
            class_val = int(val[0, 0])
            land_cover_str = WORLDCOVER_CLASSES.get(class_val, "unknown")
            return LandCoverResponse(land_cover=land_cover_str)
            
    except Exception as e:
        # If any error occurs reading the raster (e.g. out of bounds error not caught above)
        return LandCoverResponse(land_cover="unknown")

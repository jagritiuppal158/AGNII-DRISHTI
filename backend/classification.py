"""
classification.py — Rule-based classification for Agni-Drishti
"""
from typing import Dict, Any

def classify_rule_based(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify a thermal anomaly location using heuristics based on spatial context and temporal status.
    
    Expected keys in `features`:
    - infra_type (str or None): Type of nearby infrastructure (e.g., 'mine', 'pipeline', 'refinery', 'factory')
    - distance_to_infra (float or None): Distance to the infrastructure in meters
    - land_cover (str): Land cover class (e.g., 'Cropland', 'Tree cover', 'Built-up')
    - status (str): Temporal clustering status ('new', 'recurring', 'persistent')
    - detection_count (int): Number of hotspots clustered here
    - brightness (float): Average or max brightness (can be used as a secondary check)
    - confidence (float): Satellite confidence score
    """
    infra = features.get("infra_type")
    dist = features.get("distance_to_infra")
    status = features.get("status")
    land_cover = features.get("land_cover")
    
    # 1. MINING
    # Reasoning: Mines have continuous/regular thermal signatures (processing, blasting). 
    # Must be close to a known mine and have multiple detections over time.
    if infra == "mine" and status in ("recurring", "persistent"):
        return {"class": "mining", "confidence": 0.90}
        
    # 2. GAS FLARE
    # Reasoning: Pipelines and refineries routinely flare gas, creating persistent, intense thermal anomalies.
    # We require 'persistent' status because accidental fires are short-lived, while flaring is continuous.
    if infra in ("pipeline", "refinery") and status == "persistent":
        return {"class": "gas_flare", "confidence": 0.95}
        
    # 3. INDUSTRIAL FIRE
    # Reasoning: Factories or refineries with 'recurring' or 'persistent' signatures that aren't purely pipelines.
    # Refineries do flare (caught above if persistent), but if they are recurring/persistent factories, it's industrial.
    if infra in ("factory", "refinery") and status in ("recurring", "persistent"):
        return {"class": "industrial_fire", "confidence": 0.85}
        
    # 4. CROP BURNING
    # Reasoning: Post-harvest crop burning happens in 'Cropland' areas. It is usually short-lived
    # (new or recurring, but rarely persistent across months) and doesn't align with heavy industrial infra.
    if land_cover == "Cropland" and status in ("new", "recurring") and not infra:
        return {"class": "crop_burning", "confidence": 0.80}
        
    # 5. WILDFIRE
    # Reasoning: A single, isolated detection ('new') with no nearby infrastructure in non-cropland 
    # (e.g., Tree cover, Shrubland) is highly indicative of a wildfire.
    if status == "new" and not infra and land_cover in ("Tree cover", "Shrubland", "Grassland", "unknown"):
        return {"class": "wildfire", "confidence": 0.75}
        
    # FALLBACK
    # If it matches no specific strong rule, default to a lower confidence base classification
    return {"class": "unknown", "confidence": 0.0}


# --- TEST EXAMPLES ---
if __name__ == "__main__":
    tests = [
        {
            "name": "1. Mining Site",
            "features": {
                "infra_type": "mine", 
                "distance_to_infra": 200, 
                "status": "recurring", 
                "land_cover": "Bare / sparse vegetation", 
                "detection_count": 3
            }
        },
        {
            "name": "2. Gas Flare at Refinery",
            "features": {
                "infra_type": "refinery", 
                "distance_to_infra": 50, 
                "status": "persistent", 
                "land_cover": "Built-up", 
                "detection_count": 12
            }
        },
        {
            "name": "3. Stubble/Crop Burning",
            "features": {
                "infra_type": None, 
                "distance_to_infra": None, 
                "status": "new", 
                "land_cover": "Cropland", 
                "detection_count": 1
            }
        },
        {
            "name": "4. Wildfire in Forest",
            "features": {
                "infra_type": None, 
                "distance_to_infra": None, 
                "status": "new", 
                "land_cover": "Tree cover", 
                "detection_count": 1
            }
        }
    ]
    
    for t in tests:
        result = classify_rule_based(t["features"])
        print(f"Test: {t['name']}")
        print(f"  Input: {t['features']}")
        print(f"  Result: {result}\n")

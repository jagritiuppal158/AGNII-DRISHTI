"""
routers/hotspots.py — GET /hotspots and GET /hotspots/{id}

Backed by hand-written seed data covering all five classification classes
so the frontend can be built against real, stable responses today.
Replace the seed store with a DB query when Supabase is connected.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])

# ── Enums (must match API contract exactly) ───────────────────────────────────

class ClassificationClass(str, Enum):
    industrial_fire = "industrial_fire"
    wildfire        = "wildfire"
    crop_burning    = "crop_burning"
    gas_flare       = "gas_flare"
    mining          = "mining"


class RiskLevel(str, Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


# ── Response models ───────────────────────────────────────────────────────────

class Evidence(BaseModel):
    brightness_temp_kelvin: float
    frp_mw:                 float
    scan_deg:               float
    track_deg:              float
    satellite:              str
    instrument:             str
    daynight:               str   # "D" or "N"
    raw_confidence_pct:     int


class HotspotSummary(BaseModel):
    id:             str
    detected_at:    str
    latitude:       float
    longitude:      float
    region:         str
    classification: ClassificationClass
    confidence:     float
    risk_level:     RiskLevel
    location_id:    Optional[str]
    source:         str


class HotspotDetail(HotspotSummary):
    evidence:      Evidence
    thumbnail_url: Optional[str]


class HotspotListResponse(BaseModel):
    page:      int
    page_size: int
    total:     int
    results:   list[HotspotSummary]


# ── Seed data ─────────────────────────────────────────────────────────────────
# 13 hotspots — all 5 classes, all 4 risk levels, spread across Indian regions.
# Each entry is the full Detail shape; the list endpoint returns the Summary subset.

SEED_HOTSPOTS: list[dict] = [
    # ── industrial_fire ──────────────────────────────────────────
    {
        "id":             "hs-001-ind-fire-gurgaon",
        "detected_at":    "2025-09-05T08:42:00Z",
        "latitude":        28.4595,
        "longitude":       77.0266,
        "region":         "Haryana",
        "classification": "industrial_fire",
        "confidence":      0.93,
        "risk_level":     "critical",
        "location_id":    "loc-001-gurgaon-industrial",
        "source":         "FIRMS_VIIRS",
        "evidence": {
            "brightness_temp_kelvin": 368.4,
            "frp_mw":                 52.1,
            "scan_deg":               0.375,
            "track_deg":              0.375,
            "satellite":             "SNPP",
            "instrument":            "VIIRS",
            "daynight":              "D",
            "raw_confidence_pct":     93,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-001.png",
    },
    {
        "id":             "hs-002-ind-fire-surat",
        "detected_at":    "2025-09-04T11:15:00Z",
        "latitude":        21.1702,
        "longitude":       72.8311,
        "region":         "Gujarat",
        "classification": "industrial_fire",
        "confidence":      0.76,
        "risk_level":     "high",
        "location_id":    "loc-002-surat-textile",
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 348.2,
            "frp_mw":                 31.7,
            "scan_deg":               1.0,
            "track_deg":              1.0,
            "satellite":             "Aqua",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     76,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-002.png",
    },
    {
        "id":             "hs-003-ind-fire-chennai",
        "detected_at":    "2025-09-03T06:55:00Z",
        "latitude":        13.0827,
        "longitude":       80.2707,
        "region":         "Tamil Nadu",
        "classification": "industrial_fire",
        "confidence":      0.58,
        "risk_level":     "medium",
        "location_id":    None,
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 332.0,
            "frp_mw":                 14.3,
            "scan_deg":               1.1,
            "track_deg":              1.0,
            "satellite":             "Terra",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     58,
        },
        "thumbnail_url": None,
    },
    # ── wildfire ─────────────────────────────────────────────────
    {
        "id":             "hs-004-wildfire-uttarakhand",
        "detected_at":    "2025-09-05T14:22:00Z",
        "latitude":        30.0668,
        "longitude":       79.0193,
        "region":         "Uttarakhand",
        "classification": "wildfire",
        "confidence":      0.91,
        "risk_level":     "critical",
        "location_id":    "loc-004-uttarakhand-forest",
        "source":         "FIRMS_VIIRS",
        "evidence": {
            "brightness_temp_kelvin": 371.8,
            "frp_mw":                 88.4,
            "scan_deg":               0.375,
            "track_deg":              0.375,
            "satellite":             "NOAA-20",
            "instrument":            "VIIRS",
            "daynight":              "D",
            "raw_confidence_pct":     91,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-004.png",
    },
    {
        "id":             "hs-005-wildfire-aravalli",
        "detected_at":    "2025-09-02T10:30:00Z",
        "latitude":        24.5854,
        "longitude":       73.7125,
        "region":         "Rajasthan",
        "classification": "wildfire",
        "confidence":      0.72,
        "risk_level":     "high",
        "location_id":    None,
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 345.6,
            "frp_mw":                 27.9,
            "scan_deg":               1.0,
            "track_deg":              1.0,
            "satellite":             "Terra",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     72,
        },
        "thumbnail_url": None,
    },
    {
        "id":             "hs-006-wildfire-himachal",
        "detected_at":    "2025-08-30T07:10:00Z",
        "latitude":        31.1048,
        "longitude":       77.1734,
        "region":         "Himachal Pradesh",
        "classification": "wildfire",
        "confidence":      0.35,
        "risk_level":     "low",
        "location_id":    None,
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 318.3,
            "frp_mw":                  6.2,
            "scan_deg":               1.2,
            "track_deg":              1.1,
            "satellite":             "Aqua",
            "instrument":            "MODIS",
            "daynight":              "N",
            "raw_confidence_pct":     35,
        },
        "thumbnail_url": None,
    },
    # ── crop_burning ─────────────────────────────────────────────
    {
        "id":             "hs-007-crop-punjab",
        "detected_at":    "2025-09-05T09:05:00Z",
        "latitude":        30.7333,
        "longitude":       76.7794,
        "region":         "Punjab",
        "classification": "crop_burning",
        "confidence":      0.87,
        "risk_level":     "high",
        "location_id":    "loc-007-punjab-paddy",
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 342.5,
            "frp_mw":                 18.3,
            "scan_deg":               1.1,
            "track_deg":              1.0,
            "satellite":             "Terra",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     87,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-007.png",
    },
    {
        "id":             "hs-008-crop-haryana",
        "detected_at":    "2025-09-04T08:50:00Z",
        "latitude":        29.0588,
        "longitude":       76.0856,
        "region":         "Haryana",
        "classification": "crop_burning",
        "confidence":      0.61,
        "risk_level":     "medium",
        "location_id":    None,
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 335.1,
            "frp_mw":                 11.8,
            "scan_deg":               1.0,
            "track_deg":              1.0,
            "satellite":             "Aqua",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     61,
        },
        "thumbnail_url": None,
    },
    {
        "id":             "hs-009-crop-up",
        "detected_at":    "2025-09-03T10:20:00Z",
        "latitude":        26.8467,
        "longitude":       80.9462,
        "region":         "Uttar Pradesh",
        "classification": "crop_burning",
        "confidence":      0.79,
        "risk_level":     "high",
        "location_id":    None,
        "source":         "FIRMS_VIIRS",
        "evidence": {
            "brightness_temp_kelvin": 341.0,
            "frp_mw":                 20.5,
            "scan_deg":               0.375,
            "track_deg":              0.375,
            "satellite":             "SNPP",
            "instrument":            "VIIRS",
            "daynight":              "D",
            "raw_confidence_pct":     79,
        },
        "thumbnail_url": None,
    },
    # ── gas_flare ────────────────────────────────────────────────
    {
        "id":             "hs-010-gasflare-assam",
        "detected_at":    "2025-09-05T03:30:00Z",
        "latitude":        26.7441,
        "longitude":       94.2157,
        "region":         "Assam",
        "classification": "gas_flare",
        "confidence":      0.95,
        "risk_level":     "critical",
        "location_id":    "loc-010-assam-oilfield",
        "source":         "FIRMS_VIIRS",
        "evidence": {
            "brightness_temp_kelvin": 412.0,
            "frp_mw":                 110.6,
            "scan_deg":               0.375,
            "track_deg":              0.375,
            "satellite":             "NOAA-20",
            "instrument":            "VIIRS",
            "daynight":              "N",
            "raw_confidence_pct":     95,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-010.png",
    },
    {
        "id":             "hs-011-gasflare-gujarat",
        "detected_at":    "2025-09-01T22:10:00Z",
        "latitude":        22.3072,
        "longitude":       73.1812,
        "region":         "Gujarat",
        "classification": "gas_flare",
        "confidence":      0.54,
        "risk_level":     "medium",
        "location_id":    "loc-011-gujarat-refinery",
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 355.7,
            "frp_mw":                 40.2,
            "scan_deg":               1.0,
            "track_deg":              1.0,
            "satellite":             "Aqua",
            "instrument":            "MODIS",
            "daynight":              "N",
            "raw_confidence_pct":     54,
        },
        "thumbnail_url": None,
    },
    # ── mining ───────────────────────────────────────────────────
    {
        "id":             "hs-012-mining-jharkhand",
        "detected_at":    "2025-09-04T13:45:00Z",
        "latitude":        23.6102,
        "longitude":       85.2799,
        "region":         "Jharkhand",
        "classification": "mining",
        "confidence":      0.82,
        "risk_level":     "high",
        "location_id":    "loc-012-jharkhand-coal",
        "source":         "FIRMS_VIIRS",
        "evidence": {
            "brightness_temp_kelvin": 352.3,
            "frp_mw":                 35.8,
            "scan_deg":               0.375,
            "track_deg":              0.375,
            "satellite":             "SNPP",
            "instrument":            "VIIRS",
            "daynight":              "D",
            "raw_confidence_pct":     82,
        },
        "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/hs-012.png",
    },
    {
        "id":             "hs-013-mining-odisha",
        "detected_at":    "2025-09-02T12:00:00Z",
        "latitude":        22.0064,
        "longitude":       85.8312,
        "region":         "Odisha",
        "classification": "mining",
        "confidence":      0.48,
        "risk_level":     "medium",
        "location_id":    None,
        "source":         "FIRMS_MODIS",
        "evidence": {
            "brightness_temp_kelvin": 328.9,
            "frp_mw":                 12.1,
            "scan_deg":               1.1,
            "track_deg":              1.0,
            "satellite":             "Terra",
            "instrument":            "MODIS",
            "daynight":              "D",
            "raw_confidence_pct":     48,
        },
        "thumbnail_url": None,
    },
]

# Pre-build a lookup dict for O(1) detail fetches
_HOTSPOT_BY_ID: dict[str, dict] = {h["id"]: h for h in SEED_HOTSPOTS}

# Valid filter value sets
_VALID_CLASSES    = {c.value for c in ClassificationClass}
_VALID_RISK_LEVELS = {r.value for r in RiskLevel}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=HotspotListResponse,
    summary="List hotspots",
    description="Paginated list of thermal hotspot detections with optional filters.",
)
def list_hotspots(
    region:    Optional[str]  = Query(None, description="Filter by region name"),
    cls:       Optional[str]  = Query(None, alias="class", description="Filter by classification class"),
    risk:      Optional[str]  = Query(None, description="Filter by risk level"),
    date_from: Optional[date] = Query(None, description="Earliest detection date (YYYY-MM-DD)"),
    date_to:   Optional[date] = Query(None, description="Latest detection date (YYYY-MM-DD)"),
    page:      int            = Query(1,    ge=1, description="Page number"),
    page_size: int            = Query(50,   ge=1, le=200, description="Results per page"),
) -> HotspotListResponse:
    # ── Validate enum filters ─────────────────────────────────────
    if cls and cls not in _VALID_CLASSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_filter", "message": f"Unknown class '{cls}'. Must be one of: {sorted(_VALID_CLASSES)}"},
        )
    if risk and risk not in _VALID_RISK_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_filter", "message": f"Unknown risk '{risk}'. Must be one of: {sorted(_VALID_RISK_LEVELS)}"},
        )

    # ── Apply filters ─────────────────────────────────────────────
    results = SEED_HOTSPOTS

    if region:
        results = [h for h in results if region.lower() in h["region"].lower()]
    if cls:
        results = [h for h in results if h["classification"] == cls]
    if risk:
        results = [h for h in results if h["risk_level"] == risk]
    if date_from:
        results = [h for h in results if datetime.fromisoformat(h["detected_at"].replace("Z", "+00:00")).date() >= date_from]
    if date_to:
        results = [h for h in results if datetime.fromisoformat(h["detected_at"].replace("Z", "+00:00")).date() <= date_to]

    # ── Paginate ──────────────────────────────────────────────────
    total   = len(results)
    start   = (page - 1) * page_size
    results = results[start : start + page_size]

    # ── Shape into summary (no evidence/thumbnail) ────────────────
    summaries = [
        HotspotSummary(**{k: v for k, v in h.items() if k not in ("evidence", "thumbnail_url")})
        for h in results
    ]

    return HotspotListResponse(page=page, page_size=page_size, total=total, results=summaries)


@router.get(
    "/{hotspot_id}",
    response_model=HotspotDetail,
    summary="Hotspot detail + evidence",
    description="Full detail for a single hotspot including raw satellite evidence.",
)
def get_hotspot(hotspot_id: str) -> HotspotDetail:
    hotspot = _HOTSPOT_BY_ID.get(hotspot_id)
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"No hotspot found with id '{hotspot_id}'."},
        )
    return HotspotDetail(**hotspot)

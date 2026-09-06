"""
ingestion/firms_ingest.py — FIRMS CSV → hotspots table

Supports both MODIS and VIIRS CSV formats from NASA FIRMS:
  https://firms.modaps.eosdis.nasa.gov/active_fire/

Detection logic:
  - MODIS files have a 'brightness' column (Band 21/22 brightness temp, Kelvin)
  - VIIRS files have a 'bright_ti4' column (TI4 band brightness temp, Kelvin)

Usage:
  python -m ingestion.firms_ingest data/firms_modis_sample.csv
  python -m ingestion.firms_ingest data/firms_viirs_sample.csv
  python -m ingestion.firms_ingest data/firms_modis_sample.csv data/firms_viirs_sample.csv

Exit codes:
  0 — completed (even if some rows were skipped)
  1 — fatal error (DB connection failed, file not found, etc.)
"""

from __future__ import annotations

import csv
import logging
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras

from config import settings

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("firms_ingest")


# ── Domain types ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HotspotRow:
    """Normalised, validated hotspot ready to insert."""
    latitude:         float
    longitude:        float
    brightness:       float     # Kelvin
    confidence:       float     # 0.0 – 1.0
    satellite:        str       # e.g. "Terra", "SNPP", "NOAA-20"
    instrument:       str       # "MODIS" or "VIIRS"
    acquisition_time: datetime  # UTC


# VIIRS confidence is a categorical string; map to a numeric probability.
_VIIRS_CONFIDENCE_MAP: dict[str, float] = {
    "l": 0.30,
    "n": 0.60,
    "h": 0.90,
}


# ── CSV format detection ──────────────────────────────────────────────────────

def _detect_format(fieldnames: list[str]) -> str:
    """
    Return 'UNIFIED', 'MODIS', or 'VIIRS' based on the header columns.

    UNIFIED = the pre-normalised combined file produced by the merge step.
              Identified by having 'satellite' + 'brightness' but NO 'instrument'.
    MODIS   = raw NASA FIRMS MODIS product (has 'brightness' + 'instrument').
    VIIRS   = raw NASA FIRMS VIIRS product (has 'bright_ti4').
    """
    cols = {c.strip().lower() for c in fieldnames}
    if "bright_ti4" in cols:
        return "VIIRS"
    if "brightness" in cols and "instrument" not in cols:
        return "UNIFIED"   # simplified merged schema — no instrument column
    if "brightness" in cols:
        return "MODIS"
    raise ValueError(
        f"Cannot determine FIRMS format from columns: {sorted(cols)}. "
        "Expected 'brightness' (MODIS/UNIFIED) or 'bright_ti4' (VIIRS)."
    )


# ── Row parsers ───────────────────────────────────────────────────────────────

def _parse_acquisition_time(acq_date: str, acq_time: str) -> datetime:
    """
    Combine FIRMS acq_date (YYYY-MM-DD) and acq_time (HHMM, zero-padded)
    into a UTC-aware datetime.
    """
    time_str = acq_time.strip().zfill(4)   # '842' → '0842'
    dt_str   = f"{acq_date.strip()} {time_str}"
    return datetime.strptime(dt_str, "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)


def _parse_modis_row(row: dict, row_num: int) -> Optional[HotspotRow]:
    """Parse one MODIS CSV row. Returns None and logs a warning on any error."""
    try:
        lat        = float(row["latitude"])
        lon        = float(row["longitude"])
        brightness = float(row["brightness"])
        raw_conf   = int(row["confidence"])

        if not (-90 <= lat <= 90):
            raise ValueError(f"latitude {lat} out of range")
        if not (-180 <= lon <= 180):
            raise ValueError(f"longitude {lon} out of range")
        if not (0 <= raw_conf <= 100):
            raise ValueError(f"confidence {raw_conf} not in 0-100")

        return HotspotRow(
            latitude=lat,
            longitude=lon,
            brightness=brightness,
            confidence=round(raw_conf / 100.0, 4),
            satellite=row["satellite"].strip(),
            instrument="MODIS",
            acquisition_time=_parse_acquisition_time(row["acq_date"], row["acq_time"]),
        )
    except Exception as exc:
        log.warning("Row %d — skipping malformed MODIS row: %s | row=%s", row_num, exc, dict(row))
        return None


def _parse_unified_row(row: dict, row_num: int) -> Optional[HotspotRow]:
    """
    Parse one row from the pre-merged unified firms_sample.csv.
    Schema: latitude, longitude, brightness, confidence, satellite, acq_date, acq_time.
    confidence is already on a 0-100 numeric scale for both MODIS and VIIRS rows.
    satellite is either 'MODIS' or 'VIIRS' (the instrument/product name, not the platform).
    """
    try:
        lat        = float(row["latitude"])
        lon        = float(row["longitude"])
        brightness = float(row["brightness"])
        raw_conf   = int(row["confidence"])
        satellite  = row["satellite"].strip().upper()

        if not (-90 <= lat <= 90):
            raise ValueError(f"latitude {lat} out of range")
        if not (-180 <= lon <= 180):
            raise ValueError(f"longitude {lon} out of range")
        if not (0 <= raw_conf <= 100):
            raise ValueError(f"confidence {raw_conf} not in 0-100")
        if satellite not in ("MODIS", "VIIRS"):
            raise ValueError(f"satellite '{satellite}' must be 'MODIS' or 'VIIRS'")

        return HotspotRow(
            latitude=lat,
            longitude=lon,
            brightness=brightness,
            confidence=round(raw_conf / 100.0, 4),
            satellite=satellite,
            instrument=satellite,   # instrument = satellite product name in unified format
            acquisition_time=_parse_acquisition_time(row["acq_date"], row["acq_time"]),
        )
    except Exception as exc:
        log.warning("Row %d — skipping malformed unified row: %s | row=%s", row_num, exc, dict(row))
        return None


def _parse_viirs_row(row: dict, row_num: int) -> Optional[HotspotRow]:
    """Parse one VIIRS CSV row. Returns None and logs a warning on any error."""
    try:
        lat        = float(row["latitude"])
        lon        = float(row["longitude"])
        brightness = float(row["bright_ti4"])
        conf_str   = row["confidence"].strip().lower()

        if not (-90 <= lat <= 90):
            raise ValueError(f"latitude {lat} out of range")
        if not (-180 <= lon <= 180):
            raise ValueError(f"longitude {lon} out of range")
        if conf_str not in _VIIRS_CONFIDENCE_MAP:
            raise ValueError(
                f"confidence '{conf_str}' unknown; expected one of "
                f"{list(_VIIRS_CONFIDENCE_MAP)}"
            )

        # Normalize satellite name: any of N20, N21, SNPP should become exactly "VIIRS"
        satellite = "VIIRS"

        return HotspotRow(
            latitude=lat,
            longitude=lon,
            brightness=brightness,
            confidence=_VIIRS_CONFIDENCE_MAP[conf_str],
            satellite=satellite,
            instrument="VIIRS",
            acquisition_time=_parse_acquisition_time(row["acq_date"], row["acq_time"]),
        )
    except Exception as exc:
        log.warning("Row %d — skipping malformed VIIRS row: %s | row=%s", row_num, exc, dict(row))
        return None


# ── CSV reader ────────────────────────────────────────────────────────────────

def parse_firms_csv(path: Path) -> list[HotspotRow]:
    """
    Read a FIRMS CSV file, auto-detect MODIS vs VIIRS format,
    parse every row, skip malformed rows with a warning.
    Returns a list of valid HotspotRow objects (no deduplication yet).
    """
    log.info("Reading %s …", path)

    with path.open(newline="", encoding="utf-8") as fh:
        reader   = csv.DictReader(fh)
        fmt = _detect_format(reader.fieldnames or [])
        parser = {
            "MODIS":   _parse_modis_row,
            "VIIRS":   _parse_viirs_row,
            "UNIFIED": _parse_unified_row,
        }[fmt]
        log.info("Detected format: %s", fmt)

        rows: list[HotspotRow] = []
        for row_num, raw in enumerate(reader, start=2):   # start=2: header is row 1
            parsed = parser(raw, row_num)
            if parsed is not None:
                rows.append(parsed)

    log.info("Parsed %d valid rows from %s", len(rows), path.name)
    return rows


# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(rows: list[HotspotRow]) -> list[HotspotRow]:
    """
    Remove exact duplicates within the batch being ingested.
    'Exact' = same (latitude, longitude, acquisition_time, satellite, instrument).
    """
    seen:   set[tuple]      = set()
    unique: list[HotspotRow] = []

    for row in rows:
        key = (row.latitude, row.longitude, row.acquisition_time, row.satellite, row.instrument)
        if key in seen:
            log.warning(
                "Duplicate skipped: lat=%.4f lon=%.4f time=%s sat=%s",
                row.latitude, row.longitude, row.acquisition_time, row.satellite,
            )
        else:
            seen.add(key)
            unique.append(row)

    removed = len(rows) - len(unique)
    if removed:
        log.info("Deduplication removed %d duplicate(s); %d unique rows remain.", removed, len(unique))
    return unique


# ── Database insertion ────────────────────────────────────────────────────────

_INSERT_HOTSPOT_SQL = """
INSERT INTO hotspots (
    id,
    latitude,
    longitude,
    geom,
    brightness,
    confidence,
    satellite,
    acquisition_time,
    location_id
)
VALUES (
    %(id)s,
    %(latitude)s,
    %(longitude)s,
    ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326),
    %(brightness)s,
    %(confidence)s,
    %(satellite)s,
    %(acquisition_time)s,
    %(location_id)s
)
ON CONFLICT DO NOTHING;
"""

_FIND_LOCATION_SQL = """
SELECT id, centroid_latitude, centroid_longitude, detection_count, first_detected_at, last_detected_at 
FROM locations 
WHERE ST_DWithin(centroid_geom::geography, ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326)::geography, 500) 
ORDER BY centroid_geom <-> ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326) 
LIMIT 1;
"""

_UPDATE_LOCATION_SQL = """
UPDATE locations 
SET centroid_latitude = %(new_lat)s, 
    centroid_longitude = %(new_lon)s, 
    centroid_geom = ST_SetSRID(ST_MakePoint(%(new_lon)s, %(new_lat)s), 4326), 
    detection_count = detection_count + 1, 
    status = %(new_status)s, 
    last_detected_at = %(new_last_detected_at)s 
WHERE id = %(loc_id)s;
"""

_INSERT_LOCATION_SQL = """
INSERT INTO locations (
    centroid_latitude, 
    centroid_longitude, 
    centroid_geom, 
    first_detected_at, 
    last_detected_at, 
    detection_count, 
    status, 
    current_class, 
    current_confidence
) VALUES (
    %(latitude)s, 
    %(longitude)s, 
    ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326), 
    %(acquisition_time)s, 
    %(acquisition_time)s, 
    1, 
    'new', 
    NULL, 
    NULL
) RETURNING id;
"""


def write_to_db(rows: list[HotspotRow], db_url: str) -> None:
    """
    Insert rows into the hotspots table with location clustering.
    Each hotspot is assigned to the nearest location within 500m. If none exists, a new location is created.
    """
    if not rows:
        log.info("No rows to insert.")
        return

    log.info("Connecting to database …")
    conn = psycopg2.connect(db_url)
    try:
        with conn:  # auto-commits or rolls back on exception
            with conn.cursor() as cur:
                inserted_hotspots = 0
                for r in rows:
                    # 1. Query Nearest
                    cur.execute(_FIND_LOCATION_SQL, {"latitude": r.latitude, "longitude": r.longitude})
                    loc = cur.fetchone()
                    
                    if loc:
                        loc_id, c_lat, c_lon, count, first_dt, last_dt = loc
                        
                        # 2. Update Existing Location
                        new_lat = (c_lat * count + r.latitude) / (count + 1)
                        new_lon = (c_lon * count + r.longitude) / (count + 1)
                        new_last_detected_at = max(last_dt, r.acquisition_time)
                        
                        new_count = count + 1
                        days_span = (new_last_detected_at - first_dt).days

                        if new_count >= 6 or days_span > 30:
                            new_status = 'persistent'
                        elif new_count >= 2:
                            new_status = 'recurring'
                        else:
                            new_status = 'new'
                            
                        cur.execute(_UPDATE_LOCATION_SQL, {
                            "new_lat": new_lat,
                            "new_lon": new_lon,
                            "new_status": new_status,
                            "new_last_detected_at": new_last_detected_at,
                            "loc_id": loc_id
                        })
                        location_id = loc_id
                    else:
                        # 3. Create New Location
                        cur.execute(_INSERT_LOCATION_SQL, {
                            "latitude": r.latitude,
                            "longitude": r.longitude,
                            "acquisition_time": r.acquisition_time
                        })
                        location_id = cur.fetchone()[0]
                        
                    # 4. Insert Hotspot
                    cur.execute(_INSERT_HOTSPOT_SQL, {
                        "id": str(uuid.uuid4()),
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "brightness": r.brightness,
                        "confidence": r.confidence,
                        "satellite": r.satellite,
                        "acquisition_time": r.acquisition_time,
                        "location_id": location_id
                    })
                    inserted_hotspots += cur.rowcount
                    
        log.info("Inserted %d row(s) into hotspots with clustering.", inserted_hotspots)
    finally:
        conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

def ingest(csv_paths: list[Path]) -> None:
    """Full pipeline: parse → deduplicate → write to DB."""
    all_rows: list[HotspotRow] = []

    for path in csv_paths:
        if not path.exists():
            log.error("File not found: %s", path)
            sys.exit(1)
        all_rows.extend(parse_firms_csv(path))

    all_rows = deduplicate(all_rows)

    settings.require_supabase()   # fails fast if DB URL is still a placeholder
    write_to_db(all_rows, settings.supabase_db_url)

    log.info("Ingestion complete. Total rows written: %d", len(all_rows))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m ingestion.firms_ingest <path/to/file.csv> [file2.csv ...]\n"
            "\n"
            "Examples:\n"
            "  python -m ingestion.firms_ingest data/firms_modis_sample.csv\n"
            "  python -m ingestion.firms_ingest data/firms_viirs_sample.csv\n"
            "  python -m ingestion.firms_ingest data/firms_modis_sample.csv data/firms_viirs_sample.csv\n",
            file=sys.stderr,
        )
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    ingest(paths)

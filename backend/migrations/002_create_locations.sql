-- Migration 002: Create locations table
--
-- A "location" is a persistent real-world thermal source, built by clustering
-- hotspot detections that fall within ~500 m of each other over time.
-- Created before hotspots so hotspots can reference it via location_id.

CREATE TYPE location_status AS ENUM (
    'new',
    'recurring',
    'persistent',
    'escalated'
);

CREATE TYPE classification_class AS ENUM (
    'industrial_fire',
    'wildfire',
    'crop_burning',
    'gas_flare',
    'mining'
);

CREATE TABLE locations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Centroid of the cluster; computed from constituent hotspot positions.
    centroid_latitude   DOUBLE PRECISION    NOT NULL,
    centroid_longitude  DOUBLE PRECISION    NOT NULL,
    -- PostGIS point geometry (SRID 4326 = WGS-84), kept in sync with above.
    centroid_geom       geometry(Point, 4326) NOT NULL,

    first_detected_at   TIMESTAMPTZ         NOT NULL,
    last_detected_at    TIMESTAMPTZ         NOT NULL,
    detection_count     INTEGER             NOT NULL DEFAULT 1,

    current_class       classification_class NOT NULL,
    current_confidence  DOUBLE PRECISION    NOT NULL CHECK (current_confidence BETWEEN 0.0 AND 1.0),

    status              location_status     NOT NULL DEFAULT 'new',
    updated_at          TIMESTAMPTZ         NOT NULL DEFAULT now()
);

-- Spatial index for proximity queries used during clustering.
CREATE INDEX idx_locations_centroid_geom
    ON locations USING GIST (centroid_geom);

-- Composite index for dashboard queries filtered by class + status.
CREATE INDEX idx_locations_class_status
    ON locations (current_class, status);

COMMENT ON TABLE locations IS
    'Persistent thermal-source records built by spatially clustering hotspots within ~500 m of each other over time.';
COMMENT ON COLUMN locations.centroid_geom IS
    'PostGIS Point (SRID 4326). Always kept in sync with centroid_latitude/centroid_longitude.';
COMMENT ON COLUMN locations.detection_count IS
    'Total number of hotspot detections ever linked to this location.';
COMMENT ON COLUMN locations.status IS
    'new: first detection; recurring: 2-4 detections; persistent: 5+ detections; escalated: case opened.';

-- Migration 003: Create hotspots table
--
-- Each row is a single thermal anomaly detection event from a FIRMS satellite pass.
-- location_id is nullable; it is populated asynchronously after the clustering job
-- assigns this hotspot to a persistent location.

CREATE TABLE hotspots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Raw coordinates from the FIRMS feed.
    latitude            DOUBLE PRECISION    NOT NULL,
    longitude           DOUBLE PRECISION    NOT NULL,
    -- PostGIS point geometry (SRID 4326 = WGS-84).
    geom                geometry(Point, 4326) NOT NULL,

    -- FIRMS brightness temperature (Kelvin).
    brightness          DOUBLE PRECISION    NOT NULL,

    -- FIRMS per-pixel confidence (0.0 – 1.0, converted from the raw 0–100 pct value).
    confidence          DOUBLE PRECISION    NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),

    -- Originating satellite identifier, e.g. 'Terra', 'Aqua', 'SNPP', 'NOAA-20'.
    satellite           TEXT                NOT NULL,

    -- UTC timestamp of the satellite overpass that produced this detection.
    acquisition_time    TIMESTAMPTZ         NOT NULL,

    -- FK to the persistent location this hotspot has been clustered into.
    -- NULL until the clustering job runs.
    location_id         UUID                REFERENCES locations(id) ON DELETE SET NULL,

    created_at          TIMESTAMPTZ         NOT NULL DEFAULT now()
);

-- Required indexes (specified in project brief).
CREATE INDEX idx_hotspots_lat_lon
    ON hotspots (latitude, longitude);

CREATE INDEX idx_hotspots_location_id
    ON hotspots (location_id);

-- Spatial index for PostGIS proximity queries.
CREATE INDEX idx_hotspots_geom
    ON hotspots USING GIST (geom);

-- Time-series index — common query pattern for recent detections.
CREATE INDEX idx_hotspots_acquisition_time
    ON hotspots (acquisition_time DESC);

COMMENT ON TABLE hotspots IS
    'Individual thermal anomaly detection events ingested from the NASA FIRMS feed.';
COMMENT ON COLUMN hotspots.geom IS
    'PostGIS Point (SRID 4326). Always kept in sync with latitude/longitude.';
COMMENT ON COLUMN hotspots.location_id IS
    'Populated by the background clustering job. NULL = not yet assigned to a location.';

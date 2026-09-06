-- Migration 004: Create infra_context table
--
-- Stores infrastructure layer features (industrial zones, roads, gas fields, mines, etc.)
-- used as spatial evidence during classification. Geometry is stored as a generic
-- PostGIS geometry so it can hold Points, LineStrings, or Polygons from GIS data sources.

CREATE TYPE infra_type AS ENUM (
    'industrial_zone',
    'power_plant',
    'oil_gas_field',
    'mine',
    'agricultural_zone',
    'forest',
    'road',
    'residential',
    'other'
);

CREATE TABLE infra_context (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Generic geometry: accepts Point, LineString, Polygon, MultiPolygon, etc.
    -- SRID 4326 (WGS-84).
    geometry    geometry(Geometry, 4326)  NOT NULL,

    infra_type  infra_type                NOT NULL,

    -- Optional human-readable label (e.g. facility name, OSM tag).
    label       TEXT,

    -- Source dataset identifier (e.g. 'OSM', 'NRSC', 'MoEFCC').
    source      TEXT,

    created_at  TIMESTAMPTZ               NOT NULL DEFAULT now()
);

-- Spatial index — all queries against this table are proximity/intersection queries.
CREATE INDEX idx_infra_context_geom
    ON infra_context USING GIST (geometry);

CREATE INDEX idx_infra_context_type
    ON infra_context (infra_type);

COMMENT ON TABLE infra_context IS
    'Infrastructure layer used as spatial evidence during hotspot classification. Loaded from GIS datasets (OSM, government sources, etc.).';
COMMENT ON COLUMN infra_context.geometry IS
    'Generic PostGIS geometry (SRID 4326). Can be Point, LineString, Polygon, or Multi* variants depending on the feature type.';

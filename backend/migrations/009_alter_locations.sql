-- Migration 009: Alter locations

ALTER TABLE locations ALTER COLUMN current_class DROP NOT NULL;
ALTER TABLE locations ALTER COLUMN current_confidence DROP NOT NULL;

ALTER TABLE locations ADD COLUMN IF NOT EXISTS centroid_geom geometry(Point, 4326);
CREATE INDEX IF NOT EXISTS idx_locations_centroid_geom ON locations USING GIST(centroid_geom);

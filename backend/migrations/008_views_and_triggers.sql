-- Migration 008: Utility views and updated_at trigger
--
-- 1. Automatic updated_at maintenance for tables that need it.
-- 2. A convenience view for the analyst dashboard: latest classification joined to hotspot.

-- ─── updated_at trigger function ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to locations
DROP TRIGGER IF EXISTS set_locations_updated_at ON locations;
CREATE TRIGGER set_locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- Apply to cases
DROP TRIGGER IF EXISTS set_cases_updated_at ON cases;
CREATE TRIGGER set_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ─── View: hotspot_latest_classification ─────────────────────────────────────
-- Returns each hotspot joined to its most recent classification row.
-- Used by the /hotspots and /hotspots/{id} API endpoints.

CREATE OR REPLACE VIEW hotspot_latest_classification AS
SELECT DISTINCT ON (h.id)
    h.id                    AS hotspot_id,
    h.latitude,
    h.longitude,
    h.geom,
    h.brightness,
    h.confidence            AS raw_confidence,
    h.satellite,
    h.acquisition_time,
    h.location_id,
    c.id                    AS classification_id,
    c.class,
    c.confidence            AS classification_confidence,
    c.evidence,
    c.priority_score,
    c.created_at            AS classified_at
FROM hotspots h
LEFT JOIN classifications c ON c.hotspot_id = h.id
ORDER BY h.id, c.created_at DESC;

COMMENT ON VIEW hotspot_latest_classification IS
    'Each hotspot joined to its most recently created classification row. NULL classification columns indicate an unclassified hotspot.';

-- ─── View: location_open_case ─────────────────────────────────────────────────
-- Returns each location with its currently open case (if any).

CREATE OR REPLACE VIEW location_open_case AS
SELECT
    l.id                    AS location_id,
    l.centroid_latitude,
    l.centroid_longitude,
    l.centroid_geom,
    l.current_class,
    l.current_confidence,
    l.status                AS location_status,
    l.first_detected_at,
    l.last_detected_at,
    l.detection_count,
    c.id                    AS case_id,
    c.status                AS case_status,
    c.opened_at,
    c.updated_at            AS case_updated_at
FROM locations l
LEFT JOIN cases c ON c.location_id = l.id AND c.status != 'closed';

COMMENT ON VIEW location_open_case IS
    'Each location joined to its open (non-closed) case. case_id is NULL if no open case exists.';

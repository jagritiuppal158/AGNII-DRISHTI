-- Migration 008: Create infra_context table

CREATE TABLE infra_context (
    id SERIAL PRIMARY KEY,
    infra_type VARCHAR(255) NOT NULL,
    geom GEOMETRY(Geometry, 4326) NOT NULL
);

-- Index for joining / proximity searches
CREATE INDEX idx_infra_context_geom 
    ON infra_context USING GIST (geom);

COMMENT ON TABLE infra_context IS 'Stores industrial infrastructure features (factories, refineries, pipelines, mines).';

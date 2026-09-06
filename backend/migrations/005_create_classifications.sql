-- Migration 005: Create classifications table
--
-- Stores the model's classification output for each hotspot.
-- A hotspot may be reclassified over time (e.g. after new evidence), so multiple
-- rows per hotspot are allowed; the most recent row is the authoritative class.

CREATE TABLE classifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    hotspot_id      UUID                    NOT NULL
                        REFERENCES hotspots(id) ON DELETE CASCADE,

    -- Predicted class using the canonical five-class taxonomy.
    class           classification_class    NOT NULL,

    -- Model confidence for the predicted class (0.0 – 1.0).
    confidence      DOUBLE PRECISION        NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),

    -- Free-text summary of the evidence that drove this classification.
    -- Populated by the classifier pipeline; may reference nearby infra_context features.
    evidence        TEXT,

    -- Composite score used for triage ordering (higher = higher priority for review).
    -- Computed from confidence, FRP, recurrence count, and proximity to sensitive areas.
    priority_score  DOUBLE PRECISION        NOT NULL DEFAULT 0.0,

    created_at      TIMESTAMPTZ             NOT NULL DEFAULT now()
);

-- Required index (specified in project brief).
CREATE INDEX idx_classifications_hotspot_id
    ON classifications (hotspot_id);

-- Index for fetching the latest classification per hotspot efficiently.
CREATE INDEX idx_classifications_hotspot_created
    ON classifications (hotspot_id, created_at DESC);

-- Index for priority-ranked review queues.
CREATE INDEX idx_classifications_priority
    ON classifications (priority_score DESC);

COMMENT ON TABLE classifications IS
    'Model classification outputs per hotspot. Multiple rows per hotspot are allowed; the row with the latest created_at is authoritative.';
COMMENT ON COLUMN classifications.evidence IS
    'Human-readable rationale produced by the classifier, e.g. "Located 120 m from industrial_zone; FRP 45 MW; day-time detection."';
COMMENT ON COLUMN classifications.priority_score IS
    'Composite triage score. Higher values surface to analysts first.';

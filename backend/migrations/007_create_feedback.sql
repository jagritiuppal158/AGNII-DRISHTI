-- Migration 007: Create feedback table
--
-- Analyst verdicts on model classifications: confirm, reject, or uncertain.
-- One feedback record per analyst review session per hotspot.
-- Used to measure model accuracy and generate training labels.

CREATE TYPE analyst_verdict AS ENUM (
    'confirm',
    'reject',
    'uncertain'
);

CREATE TABLE feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    hotspot_id      UUID            NOT NULL
                        REFERENCES hotspots(id) ON DELETE CASCADE,

    analyst_verdict analyst_verdict NOT NULL,

    -- When verdict = 'reject', analyst may supply the corrected class.
    -- NULL is valid: analyst rejects the class but cannot determine the correct one.
    corrected_class classification_class,

    -- Optional free-text note from the analyst (max enforced at the application layer).
    notes           TEXT,

    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- Index for joining feedback onto hotspots/classifications.
CREATE INDEX idx_feedback_hotspot_id
    ON feedback (hotspot_id);

-- Index for aggregate accuracy reporting by verdict.
CREATE INDEX idx_feedback_verdict
    ON feedback (analyst_verdict);

COMMENT ON TABLE feedback IS
    'Analyst verdicts on model classification outputs. Drives accuracy metrics and active learning pipelines.';
COMMENT ON COLUMN feedback.corrected_class IS
    'Populated when analyst_verdict = ''reject''. NULL means the analyst disagrees but is unsure of the correct class.';

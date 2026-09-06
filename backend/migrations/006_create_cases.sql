-- Migration 006: Create cases table
--
-- An enforcement case is opened against a persistent location (not an individual hotspot).
-- Status transitions: open -> investigating -> notice_issued -> escalated -> closed.
-- Any status may also transition directly to 'closed'.

CREATE TYPE case_status AS ENUM (
    'open',
    'investigating',
    'notice_issued',
    'escalated',
    'closed'
);

CREATE TABLE cases (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    location_id UUID            NOT NULL
                    REFERENCES locations(id) ON DELETE RESTRICT,

    status      case_status     NOT NULL DEFAULT 'open',

    -- Analyst notes; appended on each PATCH, not overwritten.
    -- Stored as a JSONB array of {changed_at, status, notes} audit entries.
    notes       JSONB           NOT NULL DEFAULT '[]'::jsonb,

    opened_at   TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- Required index (specified in project brief).
CREATE INDEX idx_cases_location_id
    ON cases (location_id);

-- Index for filtering the case list by status.
CREATE INDEX idx_cases_status
    ON cases (status);

-- Partial index: quickly find open cases (most common operational query).
CREATE INDEX idx_cases_open
    ON cases (location_id)
    WHERE status = 'open';

COMMENT ON TABLE cases IS
    'Enforcement cases opened against a persistent thermal-source location.';
COMMENT ON COLUMN cases.notes IS
    'JSONB array of audit entries: [{changed_at: timestamptz, status: case_status, notes: text}]. Append-only.';
COMMENT ON COLUMN cases.location_id IS
    'ON DELETE RESTRICT: a location cannot be deleted while it has open cases.';

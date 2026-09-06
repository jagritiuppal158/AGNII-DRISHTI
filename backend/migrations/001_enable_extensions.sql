-- Migration 001: Enable required PostgreSQL extensions
-- Run this first in Supabase SQL editor before any other migration.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

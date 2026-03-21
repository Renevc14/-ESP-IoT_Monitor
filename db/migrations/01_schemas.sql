-- ============================================================
-- Migration 01: Schemas + TimescaleDB extension
-- Run this FIRST against your Supabase project
-- ============================================================

-- Enable TimescaleDB (must be done via Supabase Dashboard first:
--   Database -> Extensions -> timescaledb -> Enable)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS iot;
CREATE SCHEMA IF NOT EXISTS alerts;
CREATE SCHEMA IF NOT EXISTS security;

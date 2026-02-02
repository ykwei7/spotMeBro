-- Run this in Supabase SQL Editor to create the required tables

-- Users: store Telegram user info and their fitness goal
CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  goal TEXT,
  weight_unit TEXT DEFAULT 'lbs',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migration: add weight_unit if table already exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS weight_unit TEXT DEFAULT 'lbs';

-- Lifts: store each tracked workout
CREATE TABLE IF NOT EXISTS lifts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exercise TEXT NOT NULL,
  sets INTEGER NOT NULL,
  reps INTEGER NOT NULL,
  weight DECIMAL(10, 2) NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups by user and date
CREATE INDEX IF NOT EXISTS idx_lifts_user_date ON lifts(user_id, created_at DESC);

-- Enable RLS (Row Level Security) - users can only access their own data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE lifts ENABLE ROW LEVEL SECURITY;

-- Policies: service role bypasses RLS, but for direct client access you'd add policies
-- For bot use with service key, RLS is bypassed - ensure service key is kept secret

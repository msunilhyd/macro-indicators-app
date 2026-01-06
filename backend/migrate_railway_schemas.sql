-- ===================================================================
-- Schema Migration for Railway Database
-- Run this SQL directly in DBeaver connected to your Railway database
-- ===================================================================

-- Step 1: Create the macro_indicators schema
CREATE SCHEMA IF NOT EXISTS macro_indicators;

-- Step 2: Move tables to macro_indicators schema
ALTER TABLE public.categories SET SCHEMA macro_indicators;
ALTER TABLE public.indicators SET SCHEMA macro_indicators;
ALTER TABLE public.data_points SET SCHEMA macro_indicators;

-- Step 3: Verify the migration
SELECT 'macro_indicators schema tables:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'macro_indicators'
ORDER BY table_name;

SELECT 'Tables remaining in public schema:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

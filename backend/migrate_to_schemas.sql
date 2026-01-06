-- Migration script to separate tables into different schemas
-- Run this on your Railway PostgreSQL database

-- Step 1: Create schemas
CREATE SCHEMA IF NOT EXISTS macro_indicators;
CREATE SCHEMA IF NOT EXISTS linus_playlists;

-- Step 2: Move macro-indicators-app tables to macro_indicators schema
ALTER TABLE public.categories SET SCHEMA macro_indicators;
ALTER TABLE public.indicators SET SCHEMA macro_indicators;
ALTER TABLE public.data_points SET SCHEMA macro_indicators;

-- Step 3: Move linusplaylists tables to linus_playlists schema
ALTER TABLE public.users SET SCHEMA linus_playlists;
ALTER TABLE public.playlists SET SCHEMA linus_playlists;
ALTER TABLE public.songs SET SCHEMA linus_playlists;
ALTER TABLE public.artists SET SCHEMA linus_playlists;
ALTER TABLE public.play_history SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_songs SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_teams SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_artists SET SCHEMA linus_playlists;
ALTER TABLE public.user_playlists SET SCHEMA linus_playlists;
ALTER TABLE public.user_playlist_songs SET SCHEMA linus_playlists;
ALTER TABLE public.playlist_songs SET SCHEMA linus_playlists;
ALTER TABLE public.notifications SET SCHEMA linus_playlists;
ALTER TABLE public.notification_preferences SET SCHEMA linus_playlists;
ALTER TABLE public.entertainment SET SCHEMA linus_playlists;
ALTER TABLE public.highlights SET SCHEMA linus_playlists;
ALTER TABLE public.matches SET SCHEMA linus_playlists;
ALTER TABLE public.leagues SET SCHEMA linus_playlists;
ALTER TABLE public.fetched_dates SET SCHEMA linus_playlists;

-- Step 4: Verify the migration
-- Check macro_indicators schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'macro_indicators' 
ORDER BY table_name;

-- Check linus_playlists schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'linus_playlists' 
ORDER BY table_name;

-- Check public schema (should be empty or only have system tables)
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

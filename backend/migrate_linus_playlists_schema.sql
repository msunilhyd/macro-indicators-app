-- ===================================================================
-- Create linus_playlists schema and move tables
-- Run this SQL in Railway database using DBeaver
-- ===================================================================

-- Step 1: Create the linus_playlists schema
CREATE SCHEMA IF NOT EXISTS linus_playlists;

-- Step 2: Move all linusplaylists tables to linus_playlists schema
ALTER TABLE public.artists SET SCHEMA linus_playlists;
ALTER TABLE public.entertainment SET SCHEMA linus_playlists;
ALTER TABLE public.fetched_dates SET SCHEMA linus_playlists;
ALTER TABLE public.highlights SET SCHEMA linus_playlists;
ALTER TABLE public.leagues SET SCHEMA linus_playlists;
ALTER TABLE public.matches SET SCHEMA linus_playlists;
ALTER TABLE public.notification_preferences SET SCHEMA linus_playlists;
ALTER TABLE public.notifications SET SCHEMA linus_playlists;
ALTER TABLE public.play_history SET SCHEMA linus_playlists;
ALTER TABLE public.playlist_songs SET SCHEMA linus_playlists;
ALTER TABLE public.playlists SET SCHEMA linus_playlists;
ALTER TABLE public.songs SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_artists SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_songs SET SCHEMA linus_playlists;
ALTER TABLE public.user_favorite_teams SET SCHEMA linus_playlists;
ALTER TABLE public.user_playlist_songs SET SCHEMA linus_playlists;
ALTER TABLE public.user_playlists SET SCHEMA linus_playlists;
ALTER TABLE public.users SET SCHEMA linus_playlists;

-- Step 3: Verify
SELECT 'linus_playlists schema tables:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'linus_playlists'
ORDER BY table_name;

SELECT 'Public schema should be empty:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Lab init: create postgres superuser role so local pgBackRest/psql admin works via peer auth.
-- Runs once at first initdb as the stagepass user (which is superuser at init time).
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='postgres') THEN
    CREATE ROLE postgres SUPERUSER LOGIN;
  END IF;
END $$;

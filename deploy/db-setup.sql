-- Conference Bingo - Database Setup
-- Creates the bingo role and database with a secure password

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bingo') THEN
        CREATE ROLE bingo WITH LOGIN PASSWORD 'JlzKqq35px8Zk7kgD3Og_-tMhLVYRKxR';
    ELSE
        ALTER ROLE bingo WITH PASSWORD 'JlzKqq35px8Zk7kgD3Og_-tMhLVYRKxR';
    END IF;
END
$$;

SELECT 'CREATE DATABASE conference_bingo OWNER bingo'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'conference_bingo')\gexec

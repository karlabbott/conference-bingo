-- Conference Bingo Database Schema

BEGIN;

-- Pool of possible bingo squares.
CREATE TABLE IF NOT EXISTS bingo_squares (
    id         SERIAL PRIMARY KEY,
    text       VARCHAR(200) NOT NULL UNIQUE,
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Players identified by a session cookie + browser fingerprint.
CREATE TABLE IF NOT EXISTS players (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    fingerprint VARCHAR(64) NOT NULL UNIQUE,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_players_fingerprint ON players (fingerprint);

-- Each player gets one bingo card (5x5 grid).
-- card_data is a JSON array of 25 square IDs (row-major order, index 12 = free center).
CREATE TABLE IF NOT EXISTS player_cards (
    id         SERIAL PRIMARY KEY,
    player_id  INTEGER   NOT NULL UNIQUE REFERENCES players(id),
    card_data  JSONB     NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tracks which squares a player has marked on their card.
CREATE TABLE IF NOT EXISTS player_marks (
    id              SERIAL PRIMARY KEY,
    player_card_id  INTEGER   NOT NULL REFERENCES player_cards(id),
    square_position INTEGER   NOT NULL CHECK (square_position BETWEEN 0 AND 24),
    marked_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (player_card_id, square_position)
);

CREATE INDEX IF NOT EXISTS idx_player_marks_card ON player_marks (player_card_id);

-- Winners who have achieved bingo.
CREATE TABLE IF NOT EXISTS bingo_winners (
    id             SERIAL PRIMARY KEY,
    player_id      INTEGER     NOT NULL REFERENCES players(id),
    player_card_id INTEGER     NOT NULL REFERENCES player_cards(id),
    pattern        VARCHAR(20) NOT NULL,
    won_at         TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bingo_winners_time ON bingo_winners (won_at DESC);

-- Game sessions: allows admin to reset the game for a new talk.
CREATE TABLE IF NOT EXISTS game_sessions (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(200) NOT NULL DEFAULT 'Default Session',
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;

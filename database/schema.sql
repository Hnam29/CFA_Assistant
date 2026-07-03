-- CFA Learning Assistant Database Schema
-- SQLite

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,  -- bcrypt hash
    email       TEXT,
    phone       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    topic         TEXT    NOT NULL,
    session_type  TEXT    NOT NULL,  -- 'practice' | 'mock' | 'review'
    score         REAL,              -- 0-100
    total_q       INTEGER,
    correct_q     INTEGER,
    duration_mins REAL,
    completed     INTEGER DEFAULT 0,
    started_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    topic        TEXT NOT NULL,
    subtopic     TEXT,
    difficulty   TEXT NOT NULL,  -- 'easy' | 'medium' | 'hard'
    question_text TEXT NOT NULL,
    option_a     TEXT NOT NULL,
    option_b     TEXT NOT NULL,
    option_c     TEXT NOT NULL,
    correct_answer TEXT NOT NULL,  -- 'A' | 'B' | 'C'
    explanation  TEXT NOT NULL,
    source       TEXT DEFAULT 'ai', -- 'ai' or 'bank'
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    question_id     INTEGER NOT NULL,
    session_id      INTEGER,
    selected_answer TEXT,
    is_correct      INTEGER,  -- 0 or 1
    time_taken_secs REAL,
    answered_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id),
    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (session_id)  REFERENCES study_sessions(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL,
    role      TEXT    NOT NULL,   -- 'user' | 'assistant'
    content   TEXT    NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS scheduled_sessions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL,
    scheduled_date       DATE    NOT NULL,
    topic                TEXT    NOT NULL,
    session_type         TEXT    NOT NULL,
    reason               TEXT,
    priority             TEXT DEFAULT 'medium',  -- 'high' | 'medium' | 'low'
    status               TEXT DEFAULT 'pending', -- 'pending' | 'done' | 'skipped'
    alert_sent           INTEGER DEFAULT 0,
    creator              TEXT DEFAULT 'system',
    completed_session_id INTEGER,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (completed_session_id) REFERENCES study_sessions(id)
);

CREATE TABLE IF NOT EXISTS topic_performance (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    topic         TEXT    NOT NULL,
    avg_score     REAL    DEFAULT 0,
    sessions_done INTEGER DEFAULT 0,
    last_studied  DATETIME,
    UNIQUE(user_id, topic),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User profile: onboarding data + payment-ready subscription hooks
CREATE TABLE IF NOT EXISTS user_profiles (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER UNIQUE NOT NULL,
    full_name            TEXT,
    age                  INTEGER,
    gender               TEXT,        -- 'Male' | 'Female' | 'Prefer not to say'
    phone                TEXT,
    city                 TEXT,
    cfa_level            INTEGER DEFAULT 1,   -- 1 | 2 | 3
    exam_window          TEXT,        -- 'February' | 'May' | 'August' | 'November'
    exam_year            INTEGER,     -- e.g. 2026
    exam_date            DATE,        -- computed exact date for the window
    onboarding_done      INTEGER DEFAULT 0,
    -- ── Future payment integration hooks ────────────────────────────
    subscription_plan    TEXT DEFAULT 'free',      -- 'free' | 'pro' | 'enterprise'
    subscription_status  TEXT DEFAULT 'inactive',  -- 'inactive' | 'active' | 'cancelled' | 'past_due'
    subscription_expires DATE,
    stripe_customer_id   TEXT,        -- Stripe / payment gateway customer ID
    -- ────────────────────────────────────────────────────────────────
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Official CFA curriculum weights table
CREATE TABLE IF NOT EXISTS curriculum_weights (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    topic  TEXT    UNIQUE NOT NULL,
    weight REAL    NOT NULL
);

-- ── Database Indices for Query Optimization ───────────────────
CREATE INDEX IF NOT EXISTS idx_user_answers_user_question ON user_answers(user_id, question_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_session ON user_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_answered_at ON user_answers(answered_at);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_started ON study_sessions(user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_sessions_lookup ON scheduled_sessions(user_id, scheduled_date, status);
CREATE INDEX IF NOT EXISTS idx_questions_lookup ON questions(topic, subtopic, difficulty);
CREATE INDEX IF NOT EXISTS idx_chat_history_lookup ON chat_history(user_id, timestamp);

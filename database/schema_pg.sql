-- CFA Learning Assistant Database Schema for PostgreSQL (Supabase)

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(255) UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic         TEXT NOT NULL,
    session_type  VARCHAR(50) NOT NULL,
    score         REAL,
    total_q       INTEGER,
    correct_q     INTEGER,
    duration_mins REAL,
    completed     INTEGER DEFAULT 0,
    session_state TEXT,
    started_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id           SERIAL PRIMARY KEY,
    topic        TEXT NOT NULL,
    subtopic     TEXT,
    difficulty   VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    option_a     TEXT NOT NULL,
    option_b     TEXT NOT NULL,
    option_c     TEXT NOT NULL,
    correct_answer VARCHAR(5) NOT NULL,
    explanation  TEXT NOT NULL,
    source       VARCHAR(50) DEFAULT 'ai',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_answers (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    session_id      INTEGER REFERENCES study_sessions(id) ON DELETE SET NULL,
    selected_answer VARCHAR(5),
    is_correct      INTEGER,
    time_taken_secs REAL,
    answered_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role      VARCHAR(50) NOT NULL,
    content   TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheduled_sessions (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_date       DATE NOT NULL,
    topic                TEXT NOT NULL,
    session_type         VARCHAR(50) NOT NULL,
    reason               TEXT,
    priority             VARCHAR(50) DEFAULT 'medium',
    status               VARCHAR(50) DEFAULT 'pending',
    alert_sent           INTEGER DEFAULT 0,
    creator              VARCHAR(50) DEFAULT 'system',
    completed_session_id INTEGER REFERENCES study_sessions(id) ON DELETE SET NULL,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_performance (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic         TEXT NOT NULL,
    avg_score     REAL DEFAULT 0,
    sessions_done INTEGER DEFAULT 0,
    last_studied  TIMESTAMP,
    UNIQUE(user_id, topic)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name            TEXT,
    age                  INTEGER,
    gender               VARCHAR(50),
    phone                TEXT,
    city                 TEXT,
    cfa_level            INTEGER DEFAULT 1,
    exam_window          TEXT,
    exam_year            INTEGER,
    exam_date            DATE,
    onboarding_done      INTEGER DEFAULT 0,
    subscription_plan    TEXT DEFAULT 'free',
    subscription_status  TEXT DEFAULT 'inactive',
    subscription_expires DATE,
    stripe_customer_id   TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS curriculum_weights (
    id     SERIAL PRIMARY KEY,
    topic  TEXT UNIQUE NOT NULL,
    weight REAL NOT NULL
);

-- Admin → user notifications
CREATE TABLE IF NOT EXISTS notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    sender     TEXT DEFAULT 'admin',
    is_read    INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_user_answers_user_question ON user_answers(user_id, question_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_session ON user_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_answered_at ON user_answers(answered_at);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_started ON study_sessions(user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_sessions_lookup ON scheduled_sessions(user_id, scheduled_date, status);
CREATE INDEX IF NOT EXISTS idx_questions_lookup ON questions(topic, subtopic, difficulty);
CREATE INDEX IF NOT EXISTS idx_chat_history_lookup ON chat_history(user_id, timestamp);

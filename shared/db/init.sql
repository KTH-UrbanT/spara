CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_logged_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_state_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    state_payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    message_id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- user or assistant or system
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS message_evidence (
    evidence_id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    evidence_payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS advisor_evaluations (
    evaluation_id SERIAL PRIMARY KEY,
    case_id TEXT NOT NULL,
    message_id INTEGER REFERENCES messages(message_id) ON DELETE CASCADE,
    advisor_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    route_correct BOOLEAN,
    building_data_correct BOOLEAN,
    recommendation_correct BOOLEAN,
    personalized BOOLEAN,
    useful BOOLEAN,
    too_generic BOOLEAN,
    needs_minor_edit BOOLEAN,
    needs_major_edit BOOLEAN,
    unsafe_or_misleading BOOLEAN,
    should_have_asked_clarification BOOLEAN,
    should_have_escalated BOOLEAN,
    technical_correctness_score INTEGER CHECK (technical_correctness_score BETWEEN 1 AND 5),
    building_specificity_score INTEGER CHECK (building_specificity_score BETWEEN 1 AND 5),
    personalization_score INTEGER CHECK (personalization_score BETWEEN 1 AND 5),
    usefulness_score INTEGER CHECK (usefulness_score BETWEEN 1 AND 5),
    justification_score INTEGER CHECK (justification_score BETWEEN 1 AND 5),
    clarity_score INTEGER CHECK (clarity_score BETWEEN 1 AND 5),
    trust_score INTEGER CHECK (trust_score BETWEEN 1 AND 5),
    safety_score INTEGER CHECK (safety_score BETWEEN 1 AND 5),
    advisor_confidence INTEGER CHECK (advisor_confidence BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    report_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    building_identifier TEXT,
    address TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_versions (
    version_id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(report_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS advisor_task_runs (
    task_run_id SERIAL PRIMARY KEY,
    case_id TEXT,
    advisor_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    condition TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    final_response TEXT,
    perceived_workload INTEGER,
    satisfaction INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(user_id) ON DELETE SET NULL,
    rating DOUBLE PRECISION NOT NULL,
    message INTEGER NOT NULL UNIQUE REFERENCES messages(message_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

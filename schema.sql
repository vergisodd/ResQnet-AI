CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    external_conversation_id TEXT,
    caller_phone TEXT,
    agent_id TEXT,
    started_at TEXT,
    duration_seconds INTEGER,
    transcript_text TEXT NOT NULL,
    raw_payload_json JSONB NOT NULL,
    analysis_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_external_id
ON conversations (external_conversation_id);

CREATE TABLE IF NOT EXISTS conversation_critical_info (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL UNIQUE REFERENCES conversations(id) ON DELETE CASCADE,
    external_conversation_id TEXT,
    caller_phone TEXT,
    agent_id TEXT,
    caller_location TEXT,
    emergency_type TEXT,
    people_affected_count INTEGER,
    people_affected_details TEXT,
    vulnerable_people JSONB NOT NULL DEFAULT '[]'::jsonb,
    critical_needs JSONB NOT NULL DEFAULT '[]'::jsonb,
    caller_safety TEXT,
    urgency_level TEXT,
    transcript_summary TEXT,
    call_summary_title TEXT,
    call_successful TEXT,
    report_completeness TEXT,
    report_completeness_rationale TEXT,
    structured_payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_critical_info_emergency_type
ON conversation_critical_info (emergency_type);

CREATE INDEX IF NOT EXISTS idx_critical_info_urgency_level
ON conversation_critical_info (urgency_level);

CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    report_text TEXT NOT NULL,
    need_type TEXT NOT NULL,
    urgency TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    people_affected INTEGER NOT NULL DEFAULT 1,
    vulnerability_indicators JSONB NOT NULL DEFAULT '[]'::jsonb,
    location_name TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'new',
    explanation TEXT NOT NULL DEFAULT '',
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE SET NULL,
    critical_info_id BIGINT REFERENCES conversation_critical_info(id) ON DELETE SET NULL,
    decision_source TEXT NOT NULL DEFAULT 'manual'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_critical_info_unique
ON incidents (critical_info_id)
WHERE critical_info_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS voice_decisions (
    id BIGSERIAL PRIMARY KEY,
    critical_info_id BIGINT NOT NULL UNIQUE REFERENCES conversation_critical_info(id) ON DELETE CASCADE,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE SET NULL,
    source TEXT NOT NULL DEFAULT 'voice',
    location_name TEXT NOT NULL,
    need_type TEXT NOT NULL,
    urgency TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    risk_tier TEXT NOT NULL,
    people_affected INTEGER NOT NULL DEFAULT 1,
    vulnerability_indicators JSONB NOT NULL DEFAULT '[]'::jsonb,
    critical_needs JSONB NOT NULL DEFAULT '[]'::jsonb,
    report_text TEXT NOT NULL,
    explanation TEXT NOT NULL DEFAULT '',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_decisions_status_priority
ON voice_decisions (status, priority_score DESC);

CREATE TABLE IF NOT EXISTS resources (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1,
    current_latitude DOUBLE PRECISION NOT NULL,
    current_longitude DOUBLE PRECISION NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS assignments (
    id BIGSERIAL PRIMARY KEY,
    incident_id BIGINT REFERENCES incidents(id) ON DELETE CASCADE,
    voice_decision_id BIGINT REFERENCES voice_decisions(id) ON DELETE CASCADE,
    resource_id BIGINT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    distance_km DOUBLE PRECISION NOT NULL,
    suitability_score DOUBLE PRECISION NOT NULL,
    assignment_reason TEXT NOT NULL,
    score_breakdown_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

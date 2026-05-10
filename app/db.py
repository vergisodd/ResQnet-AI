import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

try:
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError:
    psycopg = None
    dict_row = None

from app.scoring import risk_tier
from app.settings import settings


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def using_postgres() -> bool:
    return bool(settings.database_url)


def init_db() -> None:
    if using_postgres():
        _init_postgres()
        return
    _init_sqlite()


def _init_postgres() -> None:
    with connect() as conn:
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_external_id
            ON conversations (external_conversation_id)
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_critical_info_emergency_type
            ON conversation_critical_info (emergency_type)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_critical_info_urgency_level
            ON conversation_critical_info (urgency_level)
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS conversation_id BIGINT REFERENCES conversations(id) ON DELETE SET NULL")
        conn.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS critical_info_id BIGINT REFERENCES conversation_critical_info(id) ON DELETE SET NULL")
        conn.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS decision_source TEXT NOT NULL DEFAULT 'manual'")
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_critical_info_unique
            ON incidents (critical_info_id)
            WHERE critical_info_id IS NOT NULL
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_voice_decisions_status_priority
            ON voice_decisions (status, priority_score DESC)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 1,
                current_latitude DOUBLE PRECISION NOT NULL,
                current_longitude DOUBLE PRECISION NOT NULL,
                available BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            """
            ALTER TABLE assignments
            ADD COLUMN IF NOT EXISTS score_breakdown_json JSONB
            """
        )
        conn.execute(
            """
            ALTER TABLE assignments
            ADD COLUMN IF NOT EXISTS voice_decision_id BIGINT REFERENCES voice_decisions(id) ON DELETE CASCADE
            """
        )
        conn.execute("ALTER TABLE assignments ALTER COLUMN incident_id DROP NOT NULL")


def _init_sqlite() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_conversation_id TEXT,
                caller_phone TEXT,
                agent_id TEXT,
                started_at TEXT,
                duration_seconds INTEGER,
                transcript_text TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                analysis_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_external_id
            ON conversations (external_conversation_id)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_critical_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL UNIQUE,
                external_conversation_id TEXT,
                caller_phone TEXT,
                agent_id TEXT,
                caller_location TEXT,
                emergency_type TEXT,
                people_affected_count INTEGER,
                people_affected_details TEXT,
                vulnerable_people TEXT NOT NULL DEFAULT '[]',
                critical_needs TEXT NOT NULL DEFAULT '[]',
                caller_safety TEXT,
                urgency_level TEXT,
                transcript_summary TEXT,
                call_summary_title TEXT,
                call_successful TEXT,
                report_completeness TEXT,
                report_completeness_rationale TEXT,
                structured_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_critical_info_emergency_type
            ON conversation_critical_info (emergency_type)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_critical_info_urgency_level
            ON conversation_critical_info (urgency_level)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                report_text TEXT NOT NULL,
                need_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                priority_score INTEGER NOT NULL,
                people_affected INTEGER NOT NULL DEFAULT 1,
                vulnerability_indicators TEXT NOT NULL DEFAULT '[]',
                location_name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                explanation TEXT NOT NULL DEFAULT '',
                conversation_id INTEGER,
                critical_info_id INTEGER,
                decision_source TEXT NOT NULL DEFAULT 'manual'
            )
            """
        )
        _ensure_sqlite_column(conn, "incidents", "conversation_id", "INTEGER")
        _ensure_sqlite_column(conn, "incidents", "critical_info_id", "INTEGER")
        _ensure_sqlite_column(conn, "incidents", "decision_source", "TEXT NOT NULL DEFAULT 'manual'")
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_critical_info_unique
            ON incidents (critical_info_id)
            WHERE critical_info_id IS NOT NULL
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                critical_info_id INTEGER NOT NULL UNIQUE,
                conversation_id INTEGER,
                source TEXT NOT NULL DEFAULT 'voice',
                location_name TEXT NOT NULL,
                need_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                priority_score INTEGER NOT NULL,
                risk_tier TEXT NOT NULL,
                people_affected INTEGER NOT NULL DEFAULT 1,
                vulnerability_indicators TEXT NOT NULL DEFAULT '[]',
                critical_needs TEXT NOT NULL DEFAULT '[]',
                report_text TEXT NOT NULL,
                explanation TEXT NOT NULL DEFAULT '',
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (critical_info_id) REFERENCES conversation_critical_info(id) ON DELETE CASCADE,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_voice_decisions_status_priority
            ON voice_decisions (status, priority_score DESC)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 1,
                current_latitude REAL NOT NULL,
                current_longitude REAL NOT NULL,
                available INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER,
                voice_decision_id INTEGER,
                resource_id INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                suitability_score REAL NOT NULL,
                assignment_reason TEXT NOT NULL,
                score_breakdown_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
                FOREIGN KEY (voice_decision_id) REFERENCES voice_decisions(id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_sqlite_column(conn, "assignments", "score_breakdown_json", "TEXT")
        _ensure_sqlite_column(conn, "assignments", "voice_decision_id", "INTEGER")


def _ensure_sqlite_column(conn: sqlite3.Connection, table_name: str, column_name: str, column_type: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in columns:
        try:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise


@contextmanager
def connect() -> Iterator[Any]:
    if using_postgres():
        if psycopg is None or dict_row is None:
            raise RuntimeError("DATABASE_URL is set, but psycopg is not installed")
        conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    else:
        conn = sqlite3.connect(settings.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_conversation(
    *,
    external_conversation_id: str | None,
    caller_phone: str | None,
    agent_id: str | None,
    started_at: str | None,
    duration_seconds: int | None,
    transcript_text: str,
    raw_payload: dict[str, Any],
    analysis: dict[str, Any] | None,
) -> int:
    if using_postgres():
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO conversations (
                    external_conversation_id, caller_phone, agent_id, started_at,
                    duration_seconds, transcript_text, raw_payload_json, analysis_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    external_conversation_id,
                    caller_phone,
                    agent_id,
                    started_at,
                    duration_seconds,
                    transcript_text,
                    json.dumps(raw_payload),
                    json.dumps(analysis) if analysis else None,
                ),
            ).fetchone()
            return int(row["id"])

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO conversations (
                external_conversation_id, caller_phone, agent_id, started_at,
                duration_seconds, transcript_text, raw_payload_json, analysis_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                external_conversation_id,
                caller_phone,
                agent_id,
                started_at,
                duration_seconds,
                transcript_text,
                json.dumps(raw_payload),
                json.dumps(analysis) if analysis else None,
                utc_now(),
            ),
        )
        return int(cursor.lastrowid)


def list_conversations(limit: int = 25) -> list[dict[str, Any]]:
    with connect() as conn:
        if using_postgres():
            rows = conn.execute(
                """
                SELECT id, external_conversation_id, caller_phone, agent_id,
                       started_at, duration_seconds, transcript_text,
                       raw_payload_json, analysis_json, created_at
                FROM conversations
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, external_conversation_id, caller_phone, agent_id,
                       started_at, duration_seconds, transcript_text,
                       raw_payload_json, analysis_json, created_at
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_conversation_row_to_dict(row) for row in rows]


def get_conversation(conversation_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    return _conversation_row_to_dict(row) if row else None


def list_unprocessed_conversations(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        if using_postgres():
            rows = conn.execute(
                """
                SELECT c.id, c.external_conversation_id, c.caller_phone, c.agent_id,
                       c.started_at, c.duration_seconds, c.transcript_text,
                       c.raw_payload_json, c.analysis_json, c.created_at
                FROM conversations c
                LEFT JOIN conversation_critical_info i ON i.conversation_id = c.id
                WHERE i.id IS NULL
                ORDER BY c.id ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT c.id, c.external_conversation_id, c.caller_phone, c.agent_id,
                       c.started_at, c.duration_seconds, c.transcript_text,
                       c.raw_payload_json, c.analysis_json, c.created_at
                FROM conversations c
                LEFT JOIN conversation_critical_info i ON i.conversation_id = c.id
                WHERE i.id IS NULL
                ORDER BY c.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_conversation_row_to_dict(row) for row in rows]


def save_critical_info(info: dict[str, Any]) -> int:
    if using_postgres():
        return _save_critical_info_postgres(info)
    return _save_critical_info_sqlite(info)


def _save_critical_info_postgres(info: dict[str, Any]) -> int:
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO conversation_critical_info (
                conversation_id,
                external_conversation_id,
                caller_phone,
                agent_id,
                caller_location,
                emergency_type,
                people_affected_count,
                people_affected_details,
                vulnerable_people,
                critical_needs,
                caller_safety,
                urgency_level,
                transcript_summary,
                call_summary_title,
                call_successful,
                report_completeness,
                report_completeness_rationale,
                structured_payload_json
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                %s, %s, %s, %s, %s, %s, %s, %s::jsonb
            )
            ON CONFLICT (conversation_id) DO UPDATE SET
                external_conversation_id = EXCLUDED.external_conversation_id,
                caller_phone = EXCLUDED.caller_phone,
                agent_id = EXCLUDED.agent_id,
                caller_location = EXCLUDED.caller_location,
                emergency_type = EXCLUDED.emergency_type,
                people_affected_count = EXCLUDED.people_affected_count,
                people_affected_details = EXCLUDED.people_affected_details,
                vulnerable_people = EXCLUDED.vulnerable_people,
                critical_needs = EXCLUDED.critical_needs,
                caller_safety = EXCLUDED.caller_safety,
                urgency_level = EXCLUDED.urgency_level,
                transcript_summary = EXCLUDED.transcript_summary,
                call_summary_title = EXCLUDED.call_summary_title,
                call_successful = EXCLUDED.call_successful,
                report_completeness = EXCLUDED.report_completeness,
                report_completeness_rationale = EXCLUDED.report_completeness_rationale,
                structured_payload_json = EXCLUDED.structured_payload_json,
                updated_at = NOW()
            RETURNING id
            """,
            _critical_info_values(info),
        ).fetchone()
        return int(row["id"])


def _save_critical_info_sqlite(info: dict[str, Any]) -> int:
    now = utc_now()
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO conversation_critical_info (
                conversation_id,
                external_conversation_id,
                caller_phone,
                agent_id,
                caller_location,
                emergency_type,
                people_affected_count,
                people_affected_details,
                vulnerable_people,
                critical_needs,
                caller_safety,
                urgency_level,
                transcript_summary,
                call_summary_title,
                call_successful,
                report_completeness,
                report_completeness_rationale,
                structured_payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (conversation_id) DO UPDATE SET
                external_conversation_id = excluded.external_conversation_id,
                caller_phone = excluded.caller_phone,
                agent_id = excluded.agent_id,
                caller_location = excluded.caller_location,
                emergency_type = excluded.emergency_type,
                people_affected_count = excluded.people_affected_count,
                people_affected_details = excluded.people_affected_details,
                vulnerable_people = excluded.vulnerable_people,
                critical_needs = excluded.critical_needs,
                caller_safety = excluded.caller_safety,
                urgency_level = excluded.urgency_level,
                transcript_summary = excluded.transcript_summary,
                call_summary_title = excluded.call_summary_title,
                call_successful = excluded.call_successful,
                report_completeness = excluded.report_completeness,
                report_completeness_rationale = excluded.report_completeness_rationale,
                structured_payload_json = excluded.structured_payload_json,
                updated_at = excluded.updated_at
            RETURNING id
            """,
            (*_critical_info_values(info), now, now),
        ).fetchone()
        return int(row["id"] if isinstance(row, dict) else row[0])


def _critical_info_values(info: dict[str, Any]) -> tuple[Any, ...]:
    return (
        info.get("conversation_id"),
        info.get("external_conversation_id"),
        info.get("caller_phone"),
        info.get("agent_id"),
        info.get("caller_location"),
        info.get("emergency_type"),
        info.get("people_affected_count"),
        info.get("people_affected_details"),
        json.dumps(info.get("vulnerable_people") or []),
        json.dumps(info.get("critical_needs") or []),
        info.get("caller_safety"),
        info.get("urgency_level"),
        info.get("transcript_summary"),
        info.get("call_summary_title"),
        info.get("call_successful"),
        info.get("report_completeness"),
        info.get("report_completeness_rationale"),
        json.dumps(info.get("structured_payload") or {}),
    )


def list_critical_info(limit: int = 25) -> list[dict[str, Any]]:
    with connect() as conn:
        if using_postgres():
            rows = conn.execute(
                """
                SELECT *
                FROM conversation_critical_info
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM conversation_critical_info
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_critical_row_to_dict(row) for row in rows]


def list_critical_info_without_incident(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        if using_postgres():
            rows = conn.execute(
                """
                SELECT ci.*
                FROM conversation_critical_info ci
                LEFT JOIN incidents i ON i.critical_info_id = ci.id
                WHERE i.id IS NULL
                ORDER BY ci.id ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ci.*
                FROM conversation_critical_info ci
                LEFT JOIN incidents i ON i.critical_info_id = ci.id
                WHERE i.id IS NULL
                ORDER BY ci.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_critical_row_to_dict(row) for row in rows]


def list_critical_info_without_voice_decision(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        if using_postgres():
            rows = conn.execute(
                """
                SELECT ci.*
                FROM conversation_critical_info ci
                LEFT JOIN voice_decisions vd ON vd.critical_info_id = ci.id
                WHERE vd.id IS NULL
                ORDER BY ci.id ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ci.*
                FROM conversation_critical_info ci
                LEFT JOIN voice_decisions vd ON vd.critical_info_id = ci.id
                WHERE vd.id IS NULL
                ORDER BY ci.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_critical_row_to_dict(row) for row in rows]


def upsert_voice_decision(decision_fields: dict[str, Any]) -> dict[str, Any]:
    critical_info_id = decision_fields.get("critical_info_id")
    if critical_info_id is None:
        raise ValueError("critical_info_id is required for voice decision upsert")

    existing = get_voice_decision_by_critical_info_id(int(critical_info_id))
    if existing:
        decision_fields = {**decision_fields, "status": decision_fields.get("status", existing["status"])}
        return update_voice_decision(existing["id"], decision_fields) or existing
    return create_voice_decision(decision_fields)


def create_voice_decision(decision_fields: dict[str, Any]) -> dict[str, Any]:
    vulnerability_json = json.dumps(decision_fields.get("vulnerability_indicators") or [])
    needs_json = json.dumps(decision_fields.get("critical_needs") or [])
    if using_postgres():
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO voice_decisions (
                    critical_info_id, conversation_id, source, location_name,
                    need_type, urgency, priority_score, risk_tier,
                    people_affected, vulnerability_indicators, critical_needs,
                    report_text, explanation, latitude, longitude, status
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    decision_fields["critical_info_id"],
                    decision_fields.get("conversation_id"),
                    decision_fields.get("source", "voice"),
                    decision_fields["location_name"],
                    decision_fields["need_type"],
                    decision_fields["urgency"],
                    decision_fields["priority_score"],
                    decision_fields["risk_tier"],
                    decision_fields["people_affected"],
                    vulnerability_json,
                    needs_json,
                    decision_fields["report_text"],
                    decision_fields.get("explanation", ""),
                    decision_fields["latitude"],
                    decision_fields["longitude"],
                    decision_fields.get("status", "new"),
                ),
            ).fetchone()
        return _voice_decision_row_to_dict(row)

    now = utc_now()
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO voice_decisions (
                critical_info_id, conversation_id, source, location_name,
                need_type, urgency, priority_score, risk_tier,
                people_affected, vulnerability_indicators, critical_needs,
                report_text, explanation, latitude, longitude, status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_fields["critical_info_id"],
                decision_fields.get("conversation_id"),
                decision_fields.get("source", "voice"),
                decision_fields["location_name"],
                decision_fields["need_type"],
                decision_fields["urgency"],
                decision_fields["priority_score"],
                decision_fields["risk_tier"],
                decision_fields["people_affected"],
                vulnerability_json,
                needs_json,
                decision_fields["report_text"],
                decision_fields.get("explanation", ""),
                decision_fields["latitude"],
                decision_fields["longitude"],
                decision_fields.get("status", "new"),
                now,
                now,
            ),
        )
        voice_decision_id = int(cursor.lastrowid)
    return get_voice_decision(voice_decision_id) or {}


def update_voice_decision(voice_decision_id: int, decision_fields: dict[str, Any]) -> dict[str, Any] | None:
    vulnerability_json = json.dumps(decision_fields.get("vulnerability_indicators") or [])
    needs_json = json.dumps(decision_fields.get("critical_needs") or [])
    params = (
        decision_fields.get("conversation_id"),
        decision_fields.get("source", "voice"),
        decision_fields["location_name"],
        decision_fields["need_type"],
        decision_fields["urgency"],
        decision_fields["priority_score"],
        decision_fields["risk_tier"],
        decision_fields["people_affected"],
        vulnerability_json,
        needs_json,
        decision_fields["report_text"],
        decision_fields.get("explanation", ""),
        decision_fields["latitude"],
        decision_fields["longitude"],
        decision_fields.get("status", "new"),
        voice_decision_id,
    )
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                """
                UPDATE voice_decisions
                SET conversation_id = %s,
                    source = %s,
                    location_name = %s,
                    need_type = %s,
                    urgency = %s,
                    priority_score = %s,
                    risk_tier = %s,
                    people_affected = %s,
                    vulnerability_indicators = %s::jsonb,
                    critical_needs = %s::jsonb,
                    report_text = %s,
                    explanation = %s,
                    latitude = %s,
                    longitude = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                params,
            ).fetchone()
            return _voice_decision_row_to_dict(row) if row else None

        conn.execute(
            """
            UPDATE voice_decisions
            SET conversation_id = ?,
                source = ?,
                location_name = ?,
                need_type = ?,
                urgency = ?,
                priority_score = ?,
                risk_tier = ?,
                people_affected = ?,
                vulnerability_indicators = ?,
                critical_needs = ?,
                report_text = ?,
                explanation = ?,
                latitude = ?,
                longitude = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (*params[:-1], utc_now(), voice_decision_id),
        )
    return get_voice_decision(voice_decision_id)


def get_voice_decision(voice_decision_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute("SELECT * FROM voice_decisions WHERE id = %s", (voice_decision_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM voice_decisions WHERE id = ?", (voice_decision_id,)).fetchone()
    return _voice_decision_row_to_dict(row) if row else None


def get_voice_decision_by_critical_info_id(critical_info_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                "SELECT * FROM voice_decisions WHERE critical_info_id = %s",
                (critical_info_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM voice_decisions WHERE critical_info_id = ?",
                (critical_info_id,),
            ).fetchone()
    return _voice_decision_row_to_dict(row) if row else None


def list_voice_decisions(status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = %s" if using_postgres() else "status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    limit_sql = ""
    if limit:
        limit_sql = "LIMIT %s" if using_postgres() else "LIMIT ?"
        params.append(limit)

    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM voice_decisions
            {where}
            ORDER BY priority_score DESC, id ASC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()
    return [_voice_decision_row_to_dict(row) for row in rows]


def update_voice_decision_status(voice_decision_id: int, status: str) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                "UPDATE voice_decisions SET status = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (status, voice_decision_id),
            ).fetchone()
            return _voice_decision_row_to_dict(row) if row else None
        conn.execute(
            "UPDATE voice_decisions SET status = ?, updated_at = ? WHERE id = ?",
            (status, utc_now(), voice_decision_id),
        )
    return get_voice_decision(voice_decision_id)


def create_incident(
    *,
    source: str,
    report_text: str,
    need_type: str,
    urgency: str,
    priority_score: int,
    people_affected: int,
    vulnerability_indicators: list[str],
    location_name: str,
    latitude: float,
    longitude: float,
    status: str = "new",
    explanation: str = "",
    conversation_id: int | None = None,
    critical_info_id: int | None = None,
    decision_source: str = "manual",
) -> dict[str, Any]:
    vulnerability_json = json.dumps(vulnerability_indicators)
    if using_postgres():
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO incidents (
                    source, report_text, need_type, urgency, priority_score,
                    people_affected, vulnerability_indicators, location_name,
                    latitude, longitude, status, explanation,
                    conversation_id, critical_info_id, decision_source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    source,
                    report_text,
                    need_type,
                    urgency,
                    priority_score,
                    people_affected,
                    vulnerability_json,
                    location_name,
                    latitude,
                    longitude,
                    status,
                    explanation,
                    conversation_id,
                    critical_info_id,
                    decision_source,
                ),
            ).fetchone()
        return _incident_row_to_dict(row)

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents (
                source, report_text, need_type, urgency, priority_score,
                people_affected, vulnerability_indicators, location_name,
                latitude, longitude, created_at, status, explanation,
                conversation_id, critical_info_id, decision_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source,
                report_text,
                need_type,
                urgency,
                priority_score,
                people_affected,
                vulnerability_json,
                location_name,
                latitude,
                longitude,
                utc_now(),
                status,
                explanation,
                conversation_id,
                critical_info_id,
                decision_source,
            ),
        )
        incident_id = int(cursor.lastrowid)
    return get_incident(incident_id) or {}


def upsert_incident_from_critical_info(decision_fields: dict[str, Any]) -> dict[str, Any]:
    critical_info_id = decision_fields.get("critical_info_id")
    if critical_info_id is None:
        raise ValueError("critical_info_id is required for voice-derived incident upsert")

    existing = get_incident_by_critical_info_id(int(critical_info_id))
    if existing:
        return update_incident_decision_fields(existing["id"], decision_fields) or existing

    return create_incident(
        source=decision_fields.get("source", "voice"),
        report_text=decision_fields["report_text"],
        need_type=decision_fields["need_type"],
        urgency=decision_fields["urgency"],
        priority_score=decision_fields["priority_score"],
        people_affected=decision_fields["people_affected"],
        vulnerability_indicators=decision_fields.get("vulnerability_indicators") or [],
        location_name=decision_fields["location_name"],
        latitude=decision_fields["latitude"],
        longitude=decision_fields["longitude"],
        explanation=decision_fields["explanation"],
        conversation_id=decision_fields.get("conversation_id"),
        critical_info_id=critical_info_id,
        decision_source=decision_fields.get("decision_source", "voice_critical_info"),
    )


def get_incident_by_critical_info_id(critical_info_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                "SELECT * FROM incidents WHERE critical_info_id = %s",
                (critical_info_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM incidents WHERE critical_info_id = ?",
                (critical_info_id,),
            ).fetchone()
    return _incident_row_to_dict(row) if row else None


def update_incident_decision_fields(
    incident_id: int,
    decision_fields: dict[str, Any],
) -> dict[str, Any] | None:
    vulnerability_json = json.dumps(decision_fields.get("vulnerability_indicators") or [])
    params = (
        decision_fields.get("source", "voice"),
        decision_fields["report_text"],
        decision_fields["need_type"],
        decision_fields["urgency"],
        decision_fields["priority_score"],
        decision_fields["people_affected"],
        vulnerability_json,
        decision_fields["location_name"],
        decision_fields["latitude"],
        decision_fields["longitude"],
        decision_fields["explanation"],
        decision_fields.get("conversation_id"),
        decision_fields.get("critical_info_id"),
        decision_fields.get("decision_source", "voice_critical_info"),
        incident_id,
    )
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                """
                UPDATE incidents
                SET source = %s,
                    report_text = %s,
                    need_type = %s,
                    urgency = %s,
                    priority_score = %s,
                    people_affected = %s,
                    vulnerability_indicators = %s::jsonb,
                    location_name = %s,
                    latitude = %s,
                    longitude = %s,
                    explanation = %s,
                    conversation_id = %s,
                    critical_info_id = %s,
                    decision_source = %s
                WHERE id = %s
                RETURNING *
                """,
                params,
            ).fetchone()
            return _incident_row_to_dict(row) if row else None

        conn.execute(
            """
            UPDATE incidents
            SET source = ?,
                report_text = ?,
                need_type = ?,
                urgency = ?,
                priority_score = ?,
                people_affected = ?,
                vulnerability_indicators = ?,
                location_name = ?,
                latitude = ?,
                longitude = ?,
                explanation = ?,
                conversation_id = ?,
                critical_info_id = ?,
                decision_source = ?
            WHERE id = ?
            """,
            params,
        )
    return get_incident(incident_id)


def list_incidents(status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = %s" if using_postgres() else "status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    limit_sql = ""
    if limit:
        limit_sql = "LIMIT %s" if using_postgres() else "LIMIT ?"
        params.append(limit)

    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM incidents
            {where}
            ORDER BY priority_score DESC, id ASC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()
    return [_incident_row_to_dict(row) for row in rows]


def get_incident(incident_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute("SELECT * FROM incidents WHERE id = %s", (incident_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return _incident_row_to_dict(row) if row else None


def update_incident_status(incident_id: int, status: str) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                "UPDATE incidents SET status = %s WHERE id = %s RETURNING *",
                (status, incident_id),
            ).fetchone()
            return _incident_row_to_dict(row) if row else None
        conn.execute("UPDATE incidents SET status = ? WHERE id = ?", (status, incident_id))
    return get_incident(incident_id)


def create_resource(
    *,
    name: str,
    resource_type: str,
    capacity: int,
    current_latitude: float,
    current_longitude: float,
    available: bool = True,
) -> dict[str, Any]:
    if using_postgres():
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO resources (
                    name, resource_type, capacity, current_latitude,
                    current_longitude, available
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (name, resource_type, capacity, current_latitude, current_longitude, available),
            ).fetchone()
        return _resource_row_to_dict(row)

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO resources (
                name, resource_type, capacity, current_latitude,
                current_longitude, available
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, resource_type, capacity, current_latitude, current_longitude, int(available)),
        )
        resource_id = int(cursor.lastrowid)
    return get_resource(resource_id) or {}


def list_resources(available: bool | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    where = ""
    if available is not None:
        where = "WHERE available = %s" if using_postgres() else "WHERE available = ?"
        params.append(available if using_postgres() else int(available))
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM resources
            {where}
            ORDER BY available DESC, resource_type ASC, id ASC
            """,
            tuple(params),
        ).fetchall()
    return [_resource_row_to_dict(row) for row in rows]


def get_resource(resource_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute("SELECT * FROM resources WHERE id = %s", (resource_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    return _resource_row_to_dict(row) if row else None


def update_resource_availability(resource_id: int, available: bool) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute(
                "UPDATE resources SET available = %s WHERE id = %s RETURNING *",
                (available, resource_id),
            ).fetchone()
            return _resource_row_to_dict(row) if row else None
        conn.execute(
            "UPDATE resources SET available = ? WHERE id = ?",
            (int(available), resource_id),
        )
    return get_resource(resource_id)


def create_assignment(
    *,
    incident_id: int | None = None,
    voice_decision_id: int | None = None,
    resource_id: int,
    distance_km: float,
    suitability_score: float,
    assignment_reason: str,
    score_breakdown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if incident_id is None and voice_decision_id is None:
        raise ValueError("assignment requires incident_id or voice_decision_id")

    score_breakdown_json = json.dumps(score_breakdown) if score_breakdown else None
    if using_postgres():
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO assignments (
                    incident_id, voice_decision_id, resource_id, distance_km,
                    suitability_score, assignment_reason, score_breakdown_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    incident_id,
                    voice_decision_id,
                    resource_id,
                    distance_km,
                    suitability_score,
                    assignment_reason,
                    score_breakdown_json,
                ),
            ).fetchone()
        return _assignment_row_to_dict(row)

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO assignments (
                incident_id, voice_decision_id, resource_id, distance_km,
                suitability_score, assignment_reason, score_breakdown_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                voice_decision_id,
                resource_id,
                distance_km,
                suitability_score,
                assignment_reason,
                score_breakdown_json,
                utc_now(),
            ),
        )
        assignment_id = int(cursor.lastrowid)
    return _get_assignment(assignment_id) or {}


def list_assignments() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                a.*,
                COALESCE(i.location_name, vd.location_name) AS incident_location,
                COALESCE(i.need_type, vd.need_type) AS incident_need_type,
                COALESCE(i.urgency, vd.urgency) AS incident_urgency,
                COALESCE(i.priority_score, vd.priority_score) AS incident_priority_score,
                vd.critical_info_id AS critical_info_id,
                CASE WHEN a.voice_decision_id IS NULL THEN 'demo_incident' ELSE 'voice_decision' END AS assignment_source,
                r.name AS resource_name,
                r.resource_type AS resource_type
            FROM assignments a
            LEFT JOIN incidents i ON i.id = a.incident_id
            LEFT JOIN voice_decisions vd ON vd.id = a.voice_decision_id
            JOIN resources r ON r.id = a.resource_id
            ORDER BY COALESCE(i.priority_score, vd.priority_score) DESC, a.id ASC
            """
        ).fetchall()
    return [_assignment_row_to_dict(row) for row in rows]


def clear_assignments(reset_resources: bool = True, reset_assigned_incidents: bool = True) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM assignments")
        if reset_resources:
            conn.execute("UPDATE resources SET available = TRUE" if using_postgres() else "UPDATE resources SET available = 1")
        if reset_assigned_incidents:
            conn.execute("UPDATE incidents SET status = 'new' WHERE status = 'assigned'")
            if using_postgres():
                conn.execute("UPDATE voice_decisions SET status = 'new', updated_at = NOW() WHERE status = 'assigned'")
            else:
                conn.execute(
                    "UPDATE voice_decisions SET status = 'new', updated_at = ? WHERE status = 'assigned'",
                    (utc_now(),),
                )


def clear_demo_data() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM assignments")
        if using_postgres():
            conn.execute("UPDATE voice_decisions SET status = 'new', updated_at = NOW() WHERE status = 'assigned'")
        else:
            conn.execute(
                "UPDATE voice_decisions SET status = 'new', updated_at = ? WHERE status = 'assigned'",
                (utc_now(),),
            )
        conn.execute("DELETE FROM incidents")
        conn.execute("DELETE FROM resources")


def seed_demo_data(clear_existing: bool = True) -> dict[str, Any]:
    from app.classifier import classify_report
    from app.scoring import score_incident

    if clear_existing:
        clear_demo_data()

    incident_specs = [
        ("voice", "Sixth floor residents are trapped at Riverside Towers after flood water blocked the stairwell. Two children and an elderly man need rescue.", "Riverside Towers", 43.6577, -79.3519),
        ("sms", "My grandmother needs insulin refrigerated and the apartment has no power. She is dizzy and cannot walk down the stairs.", "Regent Park North", 43.6604, -79.3631),
        ("web", "Water is entering the basement clinic. We have injured patients and backup power is failing.", "Harbourfront Clinic", 43.6389, -79.3817),
        ("simulated", "A family of five is stranded on a roof near the Don River. Roads are flooded and one person is injured.", "Lower Don Flood Zone", 43.6677, -79.3542),
        ("simulated", "Shelter at Community Hall is over capacity. We need transport for elderly residents and children.", "Eastview Community Hall", 43.6721, -79.3206),
        ("simulated", "Food supplies are gone at the temporary shelter. About 80 people have not eaten since yesterday.", "Danforth Relief Shelter", 43.6792, -79.3370),
        ("simulated", "Clean drinking water is running out in the high-rise. Several disabled residents cannot leave.", "West Don Apartments", 43.6652, -79.3832),
        ("simulated", "A flooded underpass is blocking evacuation buses from reaching west-side apartment buildings.", "King Street Underpass", 43.6449, -79.4020),
        ("simulated", "Power outage at senior residence. Oxygen machines and elevators are down.", "Maple Leaf Seniors Residence", 43.7062, -79.3978),
        ("simulated", "Two people are missing near the ravine trail after sudden flooding.", "Cedarvale Ravine", 43.6928, -79.4284),
        ("web", "Pregnant resident reports contractions and no transportation during evacuation order.", "Parkdale South", 43.6383, -79.4380),
        ("sms", "Several families need dry shelter after basement units were damaged by water.", "Scarborough Junction", 43.7164, -79.2604),
        ("voice", "First-aid station requests extra bandages and medical kits for minor injuries.", "North York First-Aid Station", 43.7615, -79.4111),
        ("simulated", "Volunteer drivers need routing support because Lakeshore Boulevard is closed by flood debris.", "Lakeshore Command Point", 43.6301, -79.4215),
    ]

    resources = [
        ("Ambulance 12", "ambulance", 2, 43.6532, -79.3832),
        ("Medical Team Bravo", "medical_team", 8, 43.6460, -79.3903),
        ("Rescue Team Alpha", "rescue_team", 12, 43.6614, -79.3554),
        ("Rescue Boat Unit 4", "rescue_team", 6, 43.6409, -79.3760),
        ("Food Truck East", "food_truck", 120, 43.6815, -79.3300),
        ("Water Supply Unit 2", "water_supply", 200, 43.6661, -79.4012),
        ("Shelter Bus North", "shelter_bus", 40, 43.7050, -79.3980),
        ("Power Team Grid 7", "power_team", 5, 43.7001, -79.3879),
        ("Shelter Bus West", "shelter_bus", 36, 43.6412, -79.4346),
        ("Ambulance 22", "ambulance", 2, 43.7590, -79.4120),
    ]

    created_incidents = []
    for source, text, location, lat, lon in incident_specs:
        classification = classify_report(text, use_ai=False)
        score = score_incident(
            report_text=text,
            need_type=classification["need_type"],
            urgency=classification["urgency"],
            people_affected=classification["people_affected"],
            vulnerability_indicators=classification["vulnerability_indicators"],
        )
        created_incidents.append(
            create_incident(
                source=source,
                report_text=text,
                need_type=classification["need_type"],
                urgency=classification["urgency"],
                priority_score=score["priority_score"],
                people_affected=classification["people_affected"],
                vulnerability_indicators=classification["vulnerability_indicators"],
                location_name=location,
                latitude=lat,
                longitude=lon,
                explanation=score["explanation"],
            )
        )

    created_resources = [
        create_resource(
            name=name,
            resource_type=resource_type,
            capacity=capacity,
            current_latitude=lat,
            current_longitude=lon,
            available=True,
        )
        for name, resource_type, capacity, lat, lon in resources
    ]

    return {
        "scenario_name": "Toronto Flood Response Simulation",
        "incidents_created": len(created_incidents),
        "resources_created": len(created_resources),
        "summary": (
            "Generated a simulated urban flood scenario with rescue, medical, "
            "shelter, water, food, power, and transportation needs across Toronto."
        ),
    }


def _get_assignment(assignment_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        if using_postgres():
            row = conn.execute("SELECT * FROM assignments WHERE id = %s", (assignment_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
    return _assignment_row_to_dict(row) if row else None


def _conversation_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    if isinstance(data.get("analysis_json"), str):
        data["analysis"] = json.loads(data.pop("analysis_json"))
    else:
        data["analysis"] = data.pop("analysis_json", None)

    if isinstance(data.get("raw_payload_json"), str):
        data["raw_payload"] = json.loads(data.pop("raw_payload_json"))
    elif "raw_payload_json" in data:
        data["raw_payload"] = data.pop("raw_payload_json")

    if data.get("created_at") is not None:
        data["created_at"] = str(data["created_at"])
    return data


def _critical_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key in ("vulnerable_people", "critical_needs", "structured_payload_json"):
        if isinstance(data.get(key), str):
            data[key] = json.loads(data[key])
    for key in ("created_at", "updated_at"):
        if data.get(key) is not None:
            data[key] = str(data[key])
    return data


def _incident_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    indicators = data.get("vulnerability_indicators", [])
    if isinstance(indicators, str):
        data["vulnerability_indicators"] = json.loads(indicators)
    elif indicators is None:
        data["vulnerability_indicators"] = []
    if data.get("created_at") is not None:
        data["created_at"] = str(data["created_at"])
    data["risk_tier"] = risk_tier(int(data.get("priority_score") or 0))
    return data


def _voice_decision_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key in ("vulnerability_indicators", "critical_needs"):
        if isinstance(data.get(key), str):
            data[key] = json.loads(data[key])
        elif data.get(key) is None:
            data[key] = []
    for key in ("created_at", "updated_at"):
        if data.get(key) is not None:
            data[key] = str(data[key])
    data["risk_tier"] = data.get("risk_tier") or risk_tier(int(data.get("priority_score") or 0))
    return data


def _resource_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    data["available"] = bool(data.get("available"))
    return data


def _assignment_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    if isinstance(data.get("score_breakdown_json"), str):
        data["score_breakdown"] = json.loads(data.pop("score_breakdown_json"))
    else:
        data["score_breakdown"] = data.pop("score_breakdown_json", None)
    if data.get("created_at") is not None:
        data["created_at"] = str(data["created_at"])
    if data.get("incident_priority_score") is not None:
        data["incident_risk_tier"] = risk_tier(int(data["incident_priority_score"]))
    return data

from typing import Any


def extract_call_fields(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data") or {}
    metadata = data.get("metadata") or {}
    analysis = data.get("analysis") or {}
    phone_call = metadata.get("phone_call") or {}

    transcript_text = _transcript_to_text(data)

    return {
        "external_conversation_id": (
            data.get("conversation_id")
            or data.get("call_id")
            or data.get("id")
            or event.get("event_id")
        ),
        "caller_phone": (
            data.get("caller_phone_number")
            or data.get("from_number")
            or phone_call.get("external_number")
        ),
        "agent_id": data.get("agent_id") or analysis.get("agent_id"),
        "started_at": metadata.get("start_time_unix_secs"),
        "duration_seconds": metadata.get("call_duration_secs")
        or data.get("duration_seconds"),
        "transcript_text": transcript_text,
    }


def _transcript_to_text(data: dict[str, Any]) -> str:
    transcript = data.get("transcript") or data.get("conversation") or []
    if isinstance(transcript, str):
        return transcript

    lines: list[str] = []
    for turn in transcript:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role") or turn.get("speaker") or "unknown"
        message = turn.get("message") or turn.get("text") or turn.get("content")
        if message:
            lines.append(f"{role}: {message}")

    return "\n".join(lines)

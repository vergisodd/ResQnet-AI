from __future__ import annotations

from typing import Any

from app.db import list_critical_info_without_voice_decision, upsert_voice_decision
from app.scoring import score_incident


DEFAULT_LATITUDE = 43.6532
DEFAULT_LONGITUDE = -79.3832

NEED_TYPES = {
    "medical",
    "food",
    "water",
    "shelter",
    "rescue",
    "power",
    "transportation",
    "other",
}

EMERGENCY_TO_NEED = {
    "medical": "medical",
    "health": "medical",
    "injury": "medical",
    "heatwave": "medical",
    "food": "food",
    "water": "water",
    "shelter": "shelter",
    "evacuation": "shelter",
    "rescue": "rescue",
    "flood": "rescue",
    "wildfire": "rescue",
    "fire": "rescue",
    "power": "power",
    "outage": "power",
    "generator": "power",
    "transport": "transportation",
    "transportation": "transportation",
}

NEED_ALIASES = {
    "medicine": "medical",
    "insulin": "medical",
    "ambulance": "medical",
    "generator": "power",
    "electricity": "power",
    "evacuation": "shelter",
    "bus": "transportation",
    "transport": "transportation",
}


def sync_decision_record_from_critical_info(critical_info: dict[str, Any]) -> dict[str, Any]:
    decision_fields = build_decision_fields_from_critical_info(critical_info)
    return upsert_voice_decision(decision_fields)


def sync_missing_decision_records(limit: int = 50) -> dict[str, Any]:
    critical_rows = list_critical_info_without_voice_decision(limit=limit)
    voice_decision_ids: list[int] = []
    for row in critical_rows:
        voice_decision = sync_decision_record_from_critical_info(row)
        voice_decision_ids.append(voice_decision["id"])
    return {"processed": len(voice_decision_ids), "voice_decision_ids": voice_decision_ids}


def build_decision_fields_from_critical_info(critical_info: dict[str, Any]) -> dict[str, Any]:
    critical_needs = _as_list(critical_info.get("critical_needs"))
    vulnerable_people = _as_list(critical_info.get("vulnerable_people"))
    people_affected = _positive_int(critical_info.get("people_affected_count"), default=1)
    need_type = _derive_need_type(critical_info.get("emergency_type"), critical_needs)
    urgency = _derive_urgency(
        critical_info.get("urgency_level"),
        critical_info.get("caller_safety"),
    )
    report_text = _build_report_text(critical_info, critical_needs)
    score = score_incident(
        report_text=report_text,
        need_type=need_type,
        urgency=urgency,
        people_affected=people_affected,
        vulnerability_indicators=vulnerable_people,
    )

    return {
        "source": "voice",
        "conversation_id": critical_info.get("conversation_id"),
        "critical_info_id": critical_info.get("id") or critical_info.get("critical_info_id"),
        "report_text": report_text,
        "need_type": need_type,
        "urgency": urgency,
        "priority_score": score["priority_score"],
        "risk_tier": score["risk_tier"],
        "people_affected": people_affected,
        "vulnerability_indicators": vulnerable_people,
        "critical_needs": critical_needs,
        "location_name": critical_info.get("caller_location") or "Voice report location pending",
        "latitude": DEFAULT_LATITUDE,
        "longitude": DEFAULT_LONGITUDE,
        "explanation": _build_explanation(critical_info, critical_needs, score["explanation"]),
    }


def _derive_need_type(emergency_type: Any, critical_needs: list[str]) -> str:
    emergency_text = str(emergency_type or "").strip().lower()
    for keyword, need_type in EMERGENCY_TO_NEED.items():
        if keyword in emergency_text:
            return need_type

    for need in critical_needs:
        normalized = need.strip().lower()
        if normalized in NEED_TYPES:
            return normalized
        if normalized in NEED_ALIASES:
            return NEED_ALIASES[normalized]
        for keyword, need_type in NEED_ALIASES.items():
            if keyword in normalized:
                return need_type
    return "other"


def _derive_urgency(urgency_level: Any, caller_safety: Any) -> str:
    text = f"{urgency_level or ''} {caller_safety or ''}".lower()
    if any(term in text for term in ("critical", "life-threatening", "immediate")):
        return "critical"
    if any(term in text for term in ("high", "urgent", "unsafe", "danger")):
        return "high"
    if any(term in text for term in ("medium", "moderate")):
        return "medium"
    if "low" in text or "safe" in text:
        return "low"
    return "medium"


def _build_report_text(critical_info: dict[str, Any], critical_needs: list[str]) -> str:
    parts = [
        critical_info.get("transcript_summary"),
        critical_info.get("people_affected_details"),
    ]
    if critical_needs:
        parts.append(f"Critical needs: {', '.join(critical_needs)}.")
    if critical_info.get("caller_safety"):
        parts.append(f"Caller safety: {critical_info['caller_safety']}.")
    if critical_info.get("urgency_level"):
        parts.append(f"Urgency: {critical_info['urgency_level']}.")
    if critical_info.get("report_completeness_rationale"):
        parts.append(f"Report completeness: {critical_info['report_completeness_rationale']}")
    text = " ".join(str(part).strip() for part in parts if part)
    return text or "Voice emergency report from structured call intake."


def _build_explanation(
    critical_info: dict[str, Any],
    critical_needs: list[str],
    score_explanation: str,
) -> str:
    source = critical_info.get("id") or critical_info.get("critical_info_id")
    location = critical_info.get("caller_location") or "location pending"
    needs = ", ".join(critical_needs) if critical_needs else "needs pending"
    return (
        f"Derived from conversation_critical_info {source}: location={location}; "
        f"critical_needs={needs}. {score_explanation}"
    )


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip().lower() for part in value.split(",") if part.strip()]
    return [str(value).strip().lower()] if str(value).strip() else []


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, parsed)

import re
from typing import Any

from app.db import list_unprocessed_conversations, save_critical_info
from app.decision_records import sync_decision_record_from_critical_info


DATA_COLLECTION_ALIASES = {
    "caller_location": ("caller_location", "location", "address"),
    "emergency_type": ("emergency_type", "type_of_emergency", "incident_type"),
    "people_affected_details": (
        "people_affected_details",
        "number_of_people_affected",
        "people_affected",
        "affected_people",
    ),
    "critical_needs_list": (
        "critical_needs_list",
        "immediate_needs",
        "needs",
        "resources_needed",
    ),
    "safety_and_urgency": (
        "safety_and_urgency",
        "urgency_level",
        "caller_safety",
        "safety",
    ),
}

VULNERABILITY_KEYWORDS = {
    "elderly": ("elderly", "senior", "grandmother", "grandfather", "older adult"),
    "children": ("child", "children", "infant", "baby", "minor"),
    "disabled": ("disabled", "disability", "wheelchair", "mobility"),
    "medical_condition": (
        "medical",
        "insulin",
        "diabetic",
        "diabetes",
        "medicine",
        "medication",
        "oxygen",
    ),
    "no_transportation": ("no transportation", "no transport", "without transportation"),
}

NEED_KEYWORDS = (
    "medical",
    "food",
    "water",
    "shelter",
    "rescue",
    "power",
    "generator",
    "transportation",
    "ambulance",
    "medicine",
)


def extract_critical_info(conversation: dict[str, Any]) -> dict[str, Any]:
    raw_payload = conversation.get("raw_payload") or {}
    data = raw_payload.get("data") or {}
    analysis = data.get("analysis") or {}
    collections = analysis.get("data_collection_results") or {}
    evaluations = analysis.get("evaluation_criteria_results") or {}
    transcript_text = conversation.get("transcript_text") or ""

    caller_location = _collection_value(collections, "caller_location")
    emergency_type = _normalize_text(_collection_value(collections, "emergency_type"))
    people_details = _collection_value(collections, "people_affected_details")
    needs_value = _collection_value(collections, "critical_needs_list")
    safety_urgency = _collection_value(collections, "safety_and_urgency")

    searchable_text = " ".join(
        value
        for value in (
            people_details,
            needs_value,
            safety_urgency,
            analysis.get("transcript_summary"),
            transcript_text,
        )
        if isinstance(value, str)
    )

    structured_payload = {
        "source": "elevenlabs_post_call_transcription",
        "data_collection_results": _compact_collection_results(collections),
        "evaluation_criteria_results": _compact_evaluation_results(evaluations),
    }

    return {
        "conversation_id": conversation.get("id"),
        "external_conversation_id": conversation.get("external_conversation_id") or data.get("conversation_id"),
        "caller_phone": conversation.get("caller_phone"),
        "agent_id": conversation.get("agent_id") or data.get("agent_id"),
        "caller_location": caller_location,
        "emergency_type": emergency_type,
        "people_affected_count": _extract_people_count(people_details or transcript_text),
        "people_affected_details": people_details,
        "vulnerable_people": _extract_vulnerable_people(searchable_text),
        "critical_needs": _extract_needs(needs_value, searchable_text),
        "caller_safety": _extract_safety(safety_urgency),
        "urgency_level": _extract_urgency(safety_urgency, searchable_text),
        "transcript_summary": analysis.get("transcript_summary"),
        "call_summary_title": analysis.get("call_summary_title"),
        "call_successful": str(analysis.get("call_successful"))
        if analysis.get("call_successful") is not None
        else None,
        "report_completeness": _evaluation_value(evaluations, "report_completeness", "result"),
        "report_completeness_rationale": _evaluation_value(evaluations, "report_completeness", "rationale"),
        "structured_payload": structured_payload,
    }


def process_unprocessed_conversations(limit: int = 50) -> dict[str, Any]:
    conversations = list_unprocessed_conversations(limit=limit)
    saved_ids: list[int] = []
    voice_decision_ids: list[int] = []
    for conversation in conversations:
        result = process_conversation(conversation)
        saved_ids.append(result["critical_info_id"])
        if result.get("voice_decision_id"):
            voice_decision_ids.append(result["voice_decision_id"])
    return {
        "processed": len(saved_ids),
        "critical_info_ids": saved_ids,
        "voice_decision_ids": voice_decision_ids,
    }


def process_conversation(conversation: dict[str, Any]) -> dict[str, int | None]:
    info = extract_critical_info(conversation)
    critical_info_id = save_critical_info(info)
    info["id"] = critical_info_id
    voice_decision = sync_decision_record_from_critical_info(info)
    return {
        "critical_info_id": critical_info_id,
        "voice_decision_id": voice_decision.get("id") if voice_decision else None,
    }


def _collection_value(collections: dict[str, Any], canonical_key: str) -> str | None:
    aliases = DATA_COLLECTION_ALIASES[canonical_key]
    for alias in aliases:
        value = _value_from_collection_item(collections.get(alias))
        if value:
            return value

    for key, item in collections.items():
        normalized_key = key.lower()
        if any(alias in normalized_key for alias in aliases):
            value = _value_from_collection_item(item)
            if value:
                return value
    return None


def _value_from_collection_item(item: Any) -> str | None:
    if isinstance(item, dict):
        value = item.get("value")
    else:
        value = item

    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(part).strip() for part in value if str(part).strip())
    return str(value).strip() or None


def _evaluation_value(evaluations: dict[str, Any], key: str, field: str) -> str | None:
    item = evaluations.get(key)
    if not isinstance(item, dict):
        return None
    value = item.get(field)
    return str(value).strip() if value is not None else None


def _extract_people_count(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(\d+)\s+(?:people|persons|individuals|residents)\b", text, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\b", text)
    return int(match.group(1)) if match else None


def _extract_vulnerable_people(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for label, keywords in VULNERABILITY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            found.append(label)
    return found


def _extract_needs(value: str | None, text: str) -> list[str]:
    source = (value or text).lower()
    needs = [keyword for keyword in NEED_KEYWORDS if keyword in source]

    if value:
        for part in re.split(r"[,;/]|\band\b", value, flags=re.I):
            cleaned = _normalize_text(part)
            if cleaned and cleaned not in needs:
                needs.append(cleaned)

    return _dedupe(needs)


def _extract_safety(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.lower()
    if "not safe" in lowered or "unsafe" in lowered or "danger" in lowered:
        return "unsafe"
    if "safe" in lowered:
        return "safe"
    return value.strip()


def _extract_urgency(value: str | None, text: str) -> str | None:
    source = f"{value or ''} {text}".lower()
    if any(term in source for term in ("life-threatening", "critical", "immediate")):
        return "critical"
    if any(term in source for term in ("urgent", "medical", "ambulance", "insulin", "oxygen")):
        return "high"
    if any(term in source for term in ("soon", "moderate", "power outage", "generator")):
        return "medium"
    if source.strip():
        return "low"
    return None


def _compact_collection_results(collections: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, item in collections.items():
        if isinstance(item, dict):
            compact[key] = {
                "value": item.get("value"),
                "rationale": item.get("rationale"),
            }
        else:
            compact[key] = {"value": item, "rationale": None}
    return compact


def _compact_evaluation_results(evaluations: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, item in evaluations.items():
        if isinstance(item, dict):
            compact[key] = {
                "result": item.get("result"),
                "rationale": item.get("rationale"),
            }
    return compact


def _normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return normalized or None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = _normalize_text(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)
    return deduped

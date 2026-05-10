from app.critical_info import process_conversation
from app.db import get_voice_decision, init_db, list_voice_decisions, save_conversation
from app.decision_records import build_decision_fields_from_critical_info


def _critical_info_payload() -> dict:
    return {
        "id": 7,
        "conversation_id": 42,
        "caller_location": "17 Milton Grove Street",
        "emergency_type": "wildfire",
        "people_affected_count": 3,
        "people_affected_details": "3 people affected, including 1 elderly person.",
        "vulnerable_people": ["elderly"],
        "critical_needs": ["transportation", "water"],
        "caller_safety": "safe",
        "urgency_level": "critical",
        "transcript_summary": "Wildfire near the caller. Grandmother needs immediate transportation.",
        "report_completeness_rationale": "Location, needs, urgency, and people affected were collected.",
    }


def test_critical_info_maps_to_decision_fields() -> None:
    decision = build_decision_fields_from_critical_info(_critical_info_payload())

    assert decision["source"] == "voice"
    assert decision["critical_info_id"] == 7
    assert decision["conversation_id"] == 42
    assert decision["need_type"] == "rescue"
    assert decision["urgency"] == "critical"
    assert decision["risk_tier"] == "Critical"
    assert decision["people_affected"] == 3
    assert decision["vulnerability_indicators"] == ["elderly"]
    assert decision["critical_needs"] == ["transportation", "water"]
    assert decision["priority_score"] >= 80
    assert decision["location_name"] == "17 Milton Grove Street"


def test_processing_conversation_creates_single_voice_decision() -> None:
    init_db()
    raw_payload = {
        "data": {
            "conversation_id": "conv_test",
            "agent_id": "agent_test",
            "analysis": {
                "data_collection_results": {
                    "caller_location": {"value": "17 Milton Grove Street"},
                    "emergency_type": {"value": "wildfire"},
                    "people_affected_details": {
                        "value": "3 people affected, including 1 elderly person."
                    },
                    "critical_needs_list": {"value": "transportation, water"},
                    "safety_and_urgency": {"value": "caller is safe, critical urgency"},
                },
                "evaluation_criteria_results": {
                    "report_completeness": {
                        "result": "success",
                        "rationale": "All required fields were collected.",
                    }
                },
                "transcript_summary": "Wildfire near the caller. Grandmother needs transportation.",
            },
        }
    }
    conversation_id = save_conversation(
        external_conversation_id="conv_test",
        caller_phone="+15555550123",
        agent_id="agent_test",
        started_at=None,
        duration_seconds=30,
        transcript_text="Caller reported a wildfire.",
        raw_payload=raw_payload,
        analysis=None,
    )
    conversation = {
        "id": conversation_id,
        "external_conversation_id": "conv_test",
        "caller_phone": "+15555550123",
        "agent_id": "agent_test",
        "transcript_text": "Caller reported a wildfire.",
        "raw_payload": raw_payload,
    }

    first = process_conversation(conversation)
    second = process_conversation(conversation)
    voice_decisions = list_voice_decisions()
    voice_decision = get_voice_decision(first["voice_decision_id"])

    assert first["critical_info_id"] == second["critical_info_id"]
    assert first["voice_decision_id"] == second["voice_decision_id"]
    assert len(voice_decisions) == 1
    assert voice_decision is not None
    assert voice_decision["critical_info_id"] == first["critical_info_id"]
    assert voice_decision["source"] == "voice"

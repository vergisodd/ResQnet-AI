from app.optimizer import haversine_km
from app.optimizer import RESOURCE_MATCHES, optimize_response
from app.critical_info import process_conversation
from app.db import create_resource, init_db, list_assignments, save_conversation, seed_demo_data


def test_haversine_toronto_distance_reasonable() -> None:
    distance = haversine_km(43.6532, -79.3832, 43.7001, -79.3879)

    assert 4.5 < distance < 6.0


def test_optimizer_uses_suitable_resources() -> None:
    init_db()
    seed_demo_data(clear_existing=True)

    result = optimize_response()
    assignments = list_assignments()

    assert result["optimization_summary"]["assignments_created"] >= 6
    assert not [
        assignment
        for assignment in assignments
        if assignment["resource_type"]
        not in RESOURCE_MATCHES.get(assignment["incident_need_type"], RESOURCE_MATCHES["other"])
    ]


def test_optimizer_returns_explainability_fields() -> None:
    init_db()
    seed_demo_data(clear_existing=True)

    result = optimize_response()
    assignment = result["assignments"][0]
    summary = result["optimization_summary"]

    assert assignment["score_breakdown"]["resource_match_score"] > 0
    assert "final_suitability_score" in assignment["score_breakdown"]
    assert "critical_incidents_assigned" in summary
    assert "average_assignment_distance_km" in summary
    assert "estimated_time_saved_percent" in summary


def test_unassigned_incidents_include_reason() -> None:
    init_db()
    seed_demo_data(clear_existing=True)

    result = optimize_response()

    assert result["unassigned_incidents"]
    assert all("unassigned_reason" in item for item in result["unassigned_incidents"])


def test_critical_incidents_prioritized_before_lower_priority() -> None:
    init_db()
    seed_demo_data(clear_existing=True)

    result = optimize_response()
    assigned_scores = [item["incident_priority_score"] for item in result["assignments"]]

    assert assigned_scores == sorted(assigned_scores, reverse=True)
    assert result["optimization_summary"]["critical_incidents_assigned"] >= 1


def test_optimizer_assigns_voice_decisions_without_incidents() -> None:
    init_db()
    raw_payload = {
        "data": {
            "conversation_id": "conv_voice_optimizer",
            "agent_id": "agent_test",
            "analysis": {
                "data_collection_results": {
                    "caller_location": {"value": "9 Charlottetown Boulevard"},
                    "emergency_type": {"value": "fire"},
                    "people_affected_details": {"value": "3 people affected, including 1 elderly person."},
                    "critical_needs_list": {"value": "rescue, medical"},
                    "safety_and_urgency": {"value": "caller is safe, critical urgency"},
                },
                "transcript_summary": "House fire with injured people inside.",
            },
        }
    }
    conversation_id = save_conversation(
        external_conversation_id="conv_voice_optimizer",
        caller_phone=None,
        agent_id="agent_test",
        started_at=None,
        duration_seconds=45,
        transcript_text="House fire with injured people inside.",
        raw_payload=raw_payload,
        analysis=None,
    )
    process_conversation(
        {
            "id": conversation_id,
            "external_conversation_id": "conv_voice_optimizer",
            "caller_phone": None,
            "agent_id": "agent_test",
            "transcript_text": "House fire with injured people inside.",
            "raw_payload": raw_payload,
        }
    )
    create_resource(
        name="Rescue Team Test",
        resource_type="rescue_team",
        capacity=8,
        current_latitude=43.6532,
        current_longitude=-79.3832,
    )

    result = optimize_response(source="voice")
    assignment = result["assignments"][0]

    assert result["optimization_summary"]["source"] == "voice"
    assert assignment["voice_decision_id"] is not None
    assert assignment["incident_id"] is None
    assert assignment["assignment_source"] == "voice_decision"
    assert assignment["incident_need_type"] == "rescue"

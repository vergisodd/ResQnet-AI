from __future__ import annotations

from typing import Any

from app.db import list_assignments, list_incidents, list_resources, list_voice_decisions
from app.scoring import risk_tier


def generate_response_plan(source: str = "auto") -> dict[str, Any]:
    voice_decisions = list_voice_decisions()
    if source == "voice":
        incidents = voice_decisions
    elif source == "demo":
        incidents = list_incidents()
    else:
        incidents = voice_decisions or list_incidents()
    resources = list_resources()
    assignments = list_assignments()

    critical = [item for item in incidents if risk_tier(item["priority_score"]) == "Critical"]
    high = [item for item in incidents if risk_tier(item["priority_score"]) == "High"]
    unresolved = [item for item in incidents if item["status"] not in {"assigned", "resolved"}]
    available_resources = [item for item in resources if item["available"]]

    executive_summary = (
        f"ResQNet AI identified {len(incidents)} active crisis reports. "
        f"{len(critical)} are critical and {len(high)} are high priority, with the largest needs "
        f"clustered around rescue, medical, shelter, water, and power support. "
        f"The current plan assigns {len(assignments)} response resources and leaves "
        f"{len(unresolved)} incidents requiring follow-up or additional capacity."
    )

    top_priorities = [
        {
            "location": incident["location_name"],
            "need_type": incident["need_type"],
            "urgency": incident["urgency"],
            "priority_score": incident["priority_score"],
            "reason": incident["explanation"],
        }
        for incident in incidents[:5]
    ]

    resource_assignments = [
        {
            "incident": assignment["incident_location"],
            "resource": assignment["resource_name"],
            "distance_km": assignment["distance_km"],
            "reason": assignment["assignment_reason"],
        }
        for assignment in assignments
    ]

    recommended_next_actions = _next_actions(critical, high, unresolved, available_resources)

    return {
        "executive_summary": executive_summary,
        "top_priorities": top_priorities,
        "resource_assignments": resource_assignments,
        "recommended_next_actions": recommended_next_actions,
        "risks_and_constraints": [
            "Simulated flood conditions may block the shortest routes, so dispatchers should verify route safety before deployment.",
            "Unassigned incidents indicate resource shortages or low resource suitability and should be escalated to mutual-aid partners.",
            "Medical, oxygen, insulin, and trapped-person reports should remain under continuous human review.",
        ],
        "communication_plan": [
            "Send assignment summary to dispatch leads and shelter coordinators.",
            "Notify field teams of priority score, vulnerability indicators, and route constraints.",
            "Publish public-facing updates for shelter, water, and transportation support without exposing private caller details.",
        ],
        "explainability_notes": [
            "Priority scores combine urgency, need severity, population affected, vulnerability indicators, and time-sensitive language.",
            "Optimization uses transparent greedy matching: highest-priority incidents are matched to the nearest suitable available resource.",
            "The prototype is deterministic when API keys are missing, making it reliable for a hackathon demo.",
        ],
        "sdg_alignment": {
            "SDG 3": "Prioritizes medical emergencies and vulnerable patients during crisis response.",
            "SDG 11": "Supports safer, more resilient city-level emergency coordination.",
            "SDG 13": "Improves response planning for climate-driven floods, storms, heat, and power disruptions.",
        },
    }


def _next_actions(
    critical: list[dict[str, Any]],
    high: list[dict[str, Any]],
    unresolved: list[dict[str, Any]],
    available_resources: list[dict[str, Any]],
) -> list[str]:
    actions = []
    if critical:
        actions.append(
            f"Immediately verify and monitor the top critical incident at {critical[0]['location_name']}."
        )
    if high:
        actions.append(
            f"Stage backup resources for {len(high)} high-priority incidents before conditions worsen."
        )
    if unresolved:
        actions.append(
            f"Request mutual aid for {len(unresolved)} unresolved incidents that lack a current assignment."
        )
    if available_resources:
        actions.append(
            f"Keep {len(available_resources)} remaining resources available for new voice or web reports."
        )
    if not actions:
        actions.append("Continue monitoring incoming reports and mark completed assignments as resolved.")
    return actions

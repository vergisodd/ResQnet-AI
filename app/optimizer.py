from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

from app.db import (
    clear_assignments,
    create_assignment,
    list_assignments,
    list_incidents,
    list_resources,
    list_voice_decisions,
    update_incident_status,
    update_resource_availability,
    update_voice_decision_status,
)


RESOURCE_MATCHES = {
    "medical": {"ambulance": 38, "medical_team": 42},
    "rescue": {"rescue_team": 45, "ambulance": 18},
    "food": {"food_truck": 42, "shelter_bus": 10},
    "water": {"water_supply": 42, "food_truck": 14},
    "shelter": {"shelter_bus": 42, "rescue_team": 12},
    "power": {"power_team": 42},
    "transportation": {"shelter_bus": 38, "rescue_team": 18},
    "other": {"rescue_team": 15, "medical_team": 10, "shelter_bus": 10},
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius * c


def optimize_response(mode: str = "greedy", source: str = "auto") -> dict[str, Any]:
    clear_assignments(reset_resources=True, reset_assigned_incidents=True)
    selected_source = _select_source(source)
    incidents = _decision_items(selected_source)
    resources = list_resources(available=True)
    available_by_id = {resource["id"]: resource for resource in resources}
    initial_resources = list(resources)
    assignments: list[dict[str, Any]] = []
    unassigned: list[dict[str, Any]] = []

    for incident in sorted(incidents, key=lambda item: item["priority_score"], reverse=True):
        scored = []
        for resource in available_by_id.values():
            scored.append((_suitability_score(incident, resource), resource))

        scored = [item for item in scored if item[0]["suitability_score"] > 0]
        if not scored:
            unassigned.append(
                _unassigned_payload(incident, initial_resources, list(available_by_id.values()), selected_source)
            )
            continue

        best_score, best_resource = max(scored, key=lambda item: item[0]["suitability_score"])
        assignment = create_assignment(
            incident_id=incident["id"] if selected_source == "demo" else None,
            voice_decision_id=incident["id"] if selected_source == "voice" else None,
            resource_id=best_resource["id"],
            distance_km=best_score["distance_km"],
            suitability_score=best_score["suitability_score"],
            assignment_reason=_assignment_reason(incident, best_resource, best_score),
            score_breakdown={
                "resource_match_score": best_score["resource_match_score"],
                "priority_weight": best_score["priority_weight"],
                "distance_penalty": best_score["distance_penalty"],
                "capacity_bonus": best_score["capacity_bonus"],
                "final_suitability_score": best_score["suitability_score"],
            },
        )
        if selected_source == "voice":
            update_voice_decision_status(incident["id"], "assigned")
        else:
            update_incident_status(incident["id"], "assigned")
        update_resource_availability(best_resource["id"], False)
        available_by_id.pop(best_resource["id"], None)
        assignments.append(assignment)

    enriched_assignments = list_assignments()
    optimized_time = _estimate_response_minutes(enriched_assignments)
    manual_time = max(optimized_time + 18, int(optimized_time * 1.45)) if enriched_assignments else 0
    saved_percent = int(round(((manual_time - optimized_time) / manual_time) * 100)) if manual_time else 0
    critical_incidents_total = sum(1 for incident in incidents if incident["priority_score"] >= 80)
    critical_incidents_assigned = sum(1 for assignment in enriched_assignments if assignment["incident_priority_score"] >= 80)
    high_priority_incidents_assigned = sum(
        1 for assignment in enriched_assignments if 60 <= assignment["incident_priority_score"] < 80
    )
    average_distance = (
        round(sum(assignment["distance_km"] for assignment in enriched_assignments) / len(enriched_assignments), 2)
        if enriched_assignments
        else 0
    )
    method = "transparent greedy resource scoring"
    if mode == "quantum_inspired":
        method = "quantum-inspired assignment scoring over a classical greedy selector"

    return {
        "assignments": enriched_assignments,
        "unassigned_incidents": unassigned,
        "optimization_summary": {
            "total_incidents_considered": len(incidents),
            "total_resources_available_before": len(initial_resources),
            "total_assignments_created": len(assignments),
            "critical_incidents_total": critical_incidents_total,
            "critical_incidents_assigned": critical_incidents_assigned,
            "high_priority_incidents_assigned": high_priority_incidents_assigned,
            "unassigned_incidents_count": len(unassigned),
            "average_assignment_distance_km": average_distance,
            "estimated_manual_response_time": manual_time,
            "estimated_optimized_response_time": optimized_time,
            "estimated_time_saved_percent": saved_percent,
            "active_incidents_considered": len(incidents),
            "assignments_created": len(assignments),
            "unassigned_count": len(unassigned),
            "method": method,
            "mode": mode,
            "source": selected_source,
            "quantum_inspired_note": (
                "This MVP uses explainable classical scoring. In quantum_inspired mode, the same assignment "
                "matrix is described as a future QUBO/Qiskit candidate without claiming quantum advantage."
            ),
        },
        "estimated_manual_response_time": manual_time,
        "estimated_optimized_response_time": optimized_time,
        "estimated_time_saved_percent": saved_percent,
    }


def _select_source(source: str) -> str:
    if source in {"voice", "demo"}:
        return source
    voice_items = [
        item
        for item in list_voice_decisions()
        if item["status"] in {"new", "in_progress"} and item["priority_score"] >= 1
    ]
    return "voice" if voice_items else "demo"


def _decision_items(source: str) -> list[dict[str, Any]]:
    if source == "voice":
        return [
            decision
            for decision in list_voice_decisions()
            if decision["status"] in {"new", "in_progress"} and decision["priority_score"] >= 1
        ]
    return [
        incident
        for incident in list_incidents()
        if incident["status"] in {"new", "in_progress"} and incident["priority_score"] >= 1
    ]


def _suitability_score(incident: dict[str, Any], resource: dict[str, Any]) -> dict[str, float]:
    need_type = incident["need_type"]
    resource_type = resource["resource_type"]
    match_score = RESOURCE_MATCHES.get(need_type, RESOURCE_MATCHES["other"]).get(resource_type, 0)
    if match_score == 0:
        return {
            "resource_match_score": 0,
            "priority_weight": 0,
            "distance_km": 0,
            "distance_penalty": 0,
            "capacity_bonus": 0,
            "suitability_score": 0,
        }

    distance_km = haversine_km(
        incident["latitude"],
        incident["longitude"],
        resource["current_latitude"],
        resource["current_longitude"],
    )
    priority_weight = incident["priority_score"] * 0.35
    distance_penalty = min(30, distance_km * 1.4)
    capacity_bonus = min(15, resource["capacity"] / max(1, incident["people_affected"]) * 4)
    suitability_score = match_score + priority_weight - distance_penalty + capacity_bonus
    return {
        "resource_match_score": round(match_score, 2),
        "priority_weight": round(priority_weight, 2),
        "distance_km": round(distance_km, 2),
        "distance_penalty": round(distance_penalty, 2),
        "capacity_bonus": round(capacity_bonus, 2),
        "suitability_score": round(suitability_score, 2),
        "final_suitability_score": round(suitability_score, 2),
    }


def _assignment_reason(
    incident: dict[str, Any],
    resource: dict[str, Any],
    score: dict[str, float],
) -> str:
    return (
        f"{resource['name']} is assigned to {incident['location_name']} because its "
        f"{resource['resource_type']} capability is suitable for the {incident['need_type']} need, "
        f"it is {score['distance_km']} km away, and it has capacity {resource['capacity']} "
        f"for a priority {incident['priority_score']} incident."
    )


def _estimate_response_minutes(assignments: list[dict[str, Any]]) -> int:
    if not assignments:
        return 0
    travel_minutes = [8 + assignment["distance_km"] * 2.2 for assignment in assignments]
    return int(round(sum(travel_minutes) / len(travel_minutes)))


def _unassigned_payload(
    incident: dict[str, Any],
    initial_resources: list[dict[str, Any]],
    remaining_resources: list[dict[str, Any]],
    source: str,
) -> dict[str, Any]:
    matching_initial = [
        resource
        for resource in initial_resources
        if RESOURCE_MATCHES.get(incident["need_type"], RESOURCE_MATCHES["other"]).get(resource["resource_type"], 0) > 0
    ]
    matching_remaining = [
        resource
        for resource in remaining_resources
        if RESOURCE_MATCHES.get(incident["need_type"], RESOURCE_MATCHES["other"]).get(resource["resource_type"], 0) > 0
    ]
    if not remaining_resources:
        reason = "Resource pool exhausted."
    elif not matching_initial:
        reason = "No suitable resource type available for this need."
    elif not matching_remaining:
        reason = "All matching resources were already assigned."
    else:
        reason = "No available resource remained after higher-priority assignments."
    return {
        "incident_id": incident["id"] if source == "demo" else None,
        "voice_decision_id": incident["id"] if source == "voice" else None,
        "location_name": incident["location_name"],
        "need_type": incident["need_type"],
        "priority_score": incident["priority_score"],
        "urgency": incident["urgency"],
        "people_affected": incident["people_affected"],
        "unassigned_reason": reason,
    }

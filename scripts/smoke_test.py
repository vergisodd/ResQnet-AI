from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_PATH", str(ROOT / "resqnet_smoke.db"))

from app.db import init_db, list_assignments, list_incidents, list_resources, seed_demo_data  # noqa: E402
from app.optimizer import optimize_response  # noqa: E402
from app.optimizer import RESOURCE_MATCHES  # noqa: E402
from app.planner import generate_response_plan  # noqa: E402


def main() -> None:
    init_db()
    seed_result = seed_demo_data(clear_existing=True)
    optimization = optimize_response()
    plan = generate_response_plan()

    incidents = list_incidents()
    resources = list_resources()
    assignments = list_assignments()

    assert len(incidents) >= 10, "Expected at least 10 seeded incidents"
    assert len(resources) == 10, "Expected 10 seeded resources"
    assert len(assignments) >= 1, "Expected optimizer to create assignments"
    assert not [
        assignment
        for assignment in assignments
        if assignment["resource_type"]
        not in RESOURCE_MATCHES.get(assignment["incident_need_type"], RESOURCE_MATCHES["other"])
    ], "Optimizer created an assignment with an unsuitable resource type"
    assert all(assignment.get("score_breakdown") for assignment in assignments), "Expected assignment score breakdowns"
    assert optimization["optimization_summary"]["critical_incidents_assigned"] >= 1
    assert optimization["optimization_summary"]["average_assignment_distance_km"] > 0
    assert plan["executive_summary"], "Expected a response plan summary"

    print("ResQNet AI smoke test passed")
    print(f"Scenario: {seed_result['scenario_name']}")
    print(f"Incidents: {len(incidents)}")
    print(f"Resources: {len(resources)}")
    print(f"Assignments: {len(assignments)}")
    print(f"Estimated time saved: {optimization['estimated_time_saved_percent']}%")


if __name__ == "__main__":
    main()

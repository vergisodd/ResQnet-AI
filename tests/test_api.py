from fastapi.testclient import TestClient

from app.main import app


def test_core_demo_api_flow() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        root = client.get("/", follow_redirects=False)
        assert root.status_code in {307, 308}
        assert root.headers["location"] == "/dashboard/"

        dashboard = client.get("/dashboard/")
        assert dashboard.status_code == 200
        assert "ResQNet AI" in dashboard.text

        simulation = client.post("/simulate-crisis")
        assert simulation.status_code == 200
        assert simulation.json()["incidents_created"] == 14
        assert simulation.json()["resources_created"] == 10

        demo_data = client.get("/demo-data")
        assert demo_data.status_code == 200
        assert len(demo_data.json()["incidents"]) == 14
        assert demo_data.json()["incidents"][0]["risk_tier"] in {"Critical", "High", "Medium", "Low"}

        manual = client.post(
            "/incidents",
            json={
                "report_text": "First-aid station requests extra bandages and medical kits for minor injuries.",
                "source": "web",
                "location_name": "Manual Test Clinic",
                "latitude": 43.653,
                "longitude": -79.383,
            },
        )
        assert manual.status_code == 200
        assert manual.json()["urgency"] == "medium"
        assert manual.json()["risk_tier"] in {"Low", "Medium"}

        optimization = client.post("/optimize-response")
        assert optimization.status_code == 200
        assert optimization.json()["optimization_summary"]["total_assignments_created"] >= 1
        assert optimization.json()["assignments"][0]["incident_risk_tier"] in {"Critical", "High", "Medium", "Low"}

        plan = client.post("/generate-plan")
        assert plan.status_code == 200
        assert plan.json()["executive_summary"]

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert metrics.json()["incident_count"] == 15

        ibm_alignment = client.get("/ibm-alignment")
        assert ibm_alignment.status_code == 200
        assert "honesty_statement" in ibm_alignment.json()

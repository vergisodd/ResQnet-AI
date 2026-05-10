from app.scoring import risk_tier, score_incident


def test_critical_rescue_scores_high() -> None:
    result = score_incident(
        report_text="Children are trapped on a roof and one person is injured.",
        need_type="rescue",
        urgency="critical",
        people_affected=6,
        vulnerability_indicators=["children", "injured"],
    )

    assert result["priority_score"] == 100
    assert result["risk_tier"] == "Critical"
    assert "rescue" in result["explanation"]


def test_risk_tiers() -> None:
    assert risk_tier(85) == "Critical"
    assert risk_tier(70) == "High"
    assert risk_tier(45) == "Medium"
    assert risk_tier(20) == "Low"


def test_mass_food_shortage_scores_high_or_critical() -> None:
    result = score_incident(
        report_text="Food supplies are gone at the temporary shelter. About 80 people have not eaten since yesterday.",
        need_type="food",
        urgency="medium",
        people_affected=80,
        vulnerability_indicators=[],
    )

    assert result["risk_tier"] in {"High", "Critical"}
    assert result["priority_score"] >= 60
    assert "Mass-care" in result["explanation"]


def test_mass_water_shortage_scores_high_or_critical() -> None:
    result = score_incident(
        report_text="Clean drinking water is running out for 80 residents in the high-rise.",
        need_type="water",
        urgency="medium",
        people_affected=80,
        vulnerability_indicators=[],
    )

    assert result["risk_tier"] in {"High", "Critical"}


def test_trapped_family_with_injury_scores_high_or_critical() -> None:
    result = score_incident(
        report_text="A family of five is stranded on a roof and one person is injured.",
        need_type="rescue",
        urgency="critical",
        people_affected=5,
        vulnerability_indicators=["injured"],
    )

    assert result["risk_tier"] in {"High", "Critical"}


def test_minor_injury_supplies_request_is_not_high() -> None:
    result = score_incident(
        report_text="First-aid station requests extra bandages and medical kits for minor injuries.",
        need_type="medical",
        urgency="high",
        people_affected=1,
        vulnerability_indicators=[],
    )

    assert result["risk_tier"] in {"Low", "Medium"}
    assert result["priority_score"] >= 15
    assert "Score moderated" in result["explanation"]


def test_elderly_couple_without_power_scores_at_least_medium() -> None:
    result = score_incident(
        report_text="Elderly couple without power in cold conditions.",
        need_type="power",
        urgency="high",
        people_affected=2,
        vulnerability_indicators=["elderly"],
    )

    assert result["priority_score"] >= 40

from app.classifier import classify_report


def test_classifier_detects_medical_vulnerability() -> None:
    result = classify_report(
        "My grandmother needs insulin and the building has no power.",
        use_ai=False,
    )

    assert result["need_type"] == "medical"
    assert result["urgency"] == "critical"
    assert "elderly" in result["vulnerability_indicators"]


def test_classifier_detects_transportation_issue() -> None:
    result = classify_report(
        "A flooded underpass is blocking ambulances from reaching the clinic.",
        use_ai=False,
    )

    assert result["need_type"] in {"transportation", "medical"}
    assert result["urgency"] in {"medium", "high"}


def test_family_of_five_beats_injury_count() -> None:
    result = classify_report(
        "A family of five is stranded on a roof near the Don River. Roads are flooded and one person is injured.",
        use_ai=False,
    )

    assert result["people_affected"] == 5
    assert result["need_type"] == "rescue"


def test_about_eighty_people_without_food() -> None:
    result = classify_report(
        "Food supplies are gone at the temporary shelter. About 80 people have not eaten since yesterday.",
        use_ai=False,
    )

    assert result["people_affected"] == 80
    assert result["need_type"] == "food"


def test_elderly_couple_count() -> None:
    result = classify_report("Elderly couple without power in cold conditions.", use_ai=False)

    assert result["people_affected"] == 2
    assert result["need_type"] == "power"


def test_three_families_count_uses_household_multiplier() -> None:
    result = classify_report("Three families need shelter after basement flooding.", use_ai=False)

    assert result["people_affected"] >= 9
    assert result["need_type"] == "shelter"


def test_minor_injuries_request_not_automatically_critical() -> None:
    result = classify_report(
        "First-aid station requests extra bandages and medical kits for minor injuries.",
        use_ai=False,
    )

    assert result["need_type"] == "medical"
    assert result["urgency"] == "medium"
    assert result["people_affected"] == 1


def test_location_hint_stops_at_context_clause() -> None:
    result = classify_report(
        "A family of five is stranded on a roof near the Don River after roads flooded.",
        use_ai=False,
    )

    assert result["location_hint"] == "Don River"

from __future__ import annotations

from typing import Any


URGENCY_POINTS = {
    "low": 10,
    "medium": 25,
    "high": 45,
    "critical": 60,
}

NEED_TYPE_POINTS = {
    "rescue": 20,
    "medical": 18,
    "water": 14,
    "shelter": 12,
    "food": 10,
    "power": 8,
    "transportation": 8,
    "other": 5,
}

VULNERABILITY_POINTS = {
    "elderly": 8,
    "children": 8,
    "disabled": 8,
    "injured": 10,
    "pregnant": 8,
    "hospital": 12,
}

TIME_SENSITIVE_KEYWORDS = {
    "trapped": 10,
    "missing": 10,
    "insulin": 8,
    "oxygen": 8,
    "bleeding": 8,
    "cannot breathe": 10,
    "roof": 8,
    "evacuation": 5,
    "no power": 5,
    "no water": 5,
}

LOW_SEVERITY_PHRASES = {
    "minor injuries": -14,
    "stable": -16,
    "non urgent": -18,
    "non-urgent": -18,
    "not urgent": -18,
    "routine": -12,
    "supplies request": -8,
    "extra bandages": -8,
    "medical kits": -6,
    "first-aid station": -8,
    "first aid station": -8,
    "no immediate danger": -15,
}

HIGH_DANGER_PHRASES = (
    "trapped",
    "roof",
    "collapse",
    "fire",
    "flood danger",
    "cannot breathe",
    "missing",
    "oxygen",
    "insulin",
)

MASS_CARE_NEEDS = {"food", "water", "shelter"}


def people_points(people_affected: int) -> int:
    if people_affected >= 16:
        return 20
    if people_affected >= 6:
        return 15
    if people_affected >= 3:
        return 10
    if people_affected >= 1:
        return 5
    return 0


def risk_tier(priority_score: int) -> str:
    if priority_score >= 80:
        return "Critical"
    if priority_score >= 60:
        return "High"
    if priority_score >= 40:
        return "Medium"
    return "Low"


def score_incident(
    *,
    report_text: str,
    need_type: str,
    urgency: str,
    people_affected: int,
    vulnerability_indicators: list[str] | None = None,
) -> dict[str, Any]:
    indicators = [indicator.lower() for indicator in (vulnerability_indicators or [])]
    text = report_text.lower()

    score = 0
    score += URGENCY_POINTS.get(urgency, 10)
    score += NEED_TYPE_POINTS.get(need_type, 5)
    score += people_points(people_affected)

    vulnerability_boosts = []
    for indicator in indicators:
        if indicator in VULNERABILITY_POINTS:
            boost = VULNERABILITY_POINTS[indicator]
            score += boost
            vulnerability_boosts.append(indicator)

    keyword_boosts = []
    for keyword, boost in TIME_SENSITIVE_KEYWORDS.items():
        if keyword in text:
            score += boost
            keyword_boosts.append(keyword)

    mass_care_boost = _mass_care_boost(need_type, urgency, people_affected)
    score += mass_care_boost

    minimum_floor = _score_floor(need_type, urgency, people_affected)
    if minimum_floor is not None:
        score = max(score, minimum_floor)

    dampening_adjustments = _severity_dampening(text, urgency, people_affected)
    for _, adjustment in dampening_adjustments:
        score += adjustment

    priority_score = min(100, max(_minimum_operational_score(need_type), int(score)))
    tier = risk_tier(priority_score)
    explanation = _build_explanation(
        priority_score=priority_score,
        tier=tier,
        urgency=urgency,
        need_type=need_type,
        people_affected=people_affected,
        vulnerability_boosts=vulnerability_boosts,
        keyword_boosts=keyword_boosts,
        mass_care_boost=mass_care_boost,
        minimum_floor=minimum_floor,
        dampening_adjustments=dampening_adjustments,
    )
    return {
        "priority_score": priority_score,
        "risk_tier": tier,
        "explanation": explanation,
        "score_breakdown": {
            "urgency": URGENCY_POINTS.get(urgency, 10),
            "need_type": NEED_TYPE_POINTS.get(need_type, 5),
            "people_affected": people_points(people_affected),
            "vulnerability_indicators": vulnerability_boosts,
            "time_sensitive_keywords": keyword_boosts,
            "mass_care_boost": mass_care_boost,
            "minimum_floor": minimum_floor,
            "severity_dampening": dampening_adjustments,
        },
    }


def _mass_care_boost(need_type: str, urgency: str, people_affected: int) -> int:
    if need_type in MASS_CARE_NEEDS:
        if people_affected >= 75 and urgency in {"medium", "high", "critical"}:
            return 22
        if people_affected >= 50:
            return 18
        if people_affected >= 25:
            return 12
    if need_type == "medical":
        if people_affected >= 50:
            return 24
        if people_affected >= 25:
            return 16
    return 0


def _score_floor(need_type: str, urgency: str, people_affected: int) -> int | None:
    if need_type in MASS_CARE_NEEDS:
        if people_affected >= 75 and urgency in {"high", "critical"}:
            return 82
        if people_affected >= 75 and urgency == "medium":
            return 70
        if people_affected >= 50:
            return 65
    if need_type == "medical" and people_affected >= 25:
        return 75 if urgency in {"high", "critical"} else 62
    return None


def _minimum_operational_score(need_type: str) -> int:
    if need_type == "other":
        return 5
    return 15


def _severity_dampening(text: str, urgency: str, people_affected: int) -> list[tuple[str, int]]:
    protected = (
        people_affected >= 50
        or urgency == "critical"
        or any(phrase in text for phrase in HIGH_DANGER_PHRASES)
    )
    adjustments = []
    for phrase, adjustment in LOW_SEVERITY_PHRASES.items():
        if phrase in text:
            applied = adjustment
            if protected:
                applied = int(round(adjustment * 0.35))
            adjustments.append((phrase, applied))
    return adjustments


def _build_explanation(
    *,
    priority_score: int,
    tier: str,
    urgency: str,
    need_type: str,
    people_affected: int,
    vulnerability_boosts: list[str],
    keyword_boosts: list[str],
    mass_care_boost: int,
    minimum_floor: int | None,
    dampening_adjustments: list[tuple[str, int]],
) -> str:
    affected = f"affecting {people_affected} people" if people_affected != 1 else "affecting 1 person"
    vulnerability_phrase = ""
    if vulnerability_boosts:
        vulnerability_phrase = f" with {', '.join(vulnerability_boosts)} present"
    keyword_phrase = ""
    if keyword_boosts:
        keyword_phrase = f" Time-sensitive signals include {', '.join(keyword_boosts[:3])}."
    mass_phrase = ""
    if mass_care_boost:
        mass_phrase = f" Mass-care scale added {mass_care_boost} points because many people are affected."
    floor_phrase = ""
    if minimum_floor is not None:
        floor_phrase = f" Score floor applied at {minimum_floor} for population-scale operational risk."
    dampening_phrase = ""
    if dampening_adjustments:
        reasons = ", ".join(reason for reason, _ in dampening_adjustments[:3])
        dampening_phrase = (
            f" Score moderated because the report includes lower-severity signals: {reasons}."
        )
    return (
        f"{tier} priority ({priority_score}/100): {urgency.title()} {need_type} report "
        f"{affected}{vulnerability_phrase}. High-impact factors include need severity, "
        f"population size, vulnerability, and operational time sensitivity.{keyword_phrase}"
        f"{mass_phrase}{floor_phrase}{dampening_phrase}"
    )

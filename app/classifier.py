from __future__ import annotations

import json
import re
from typing import Any, NamedTuple

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from app.settings import settings


NEED_KEYWORDS = {
    "rescue": ["trapped", "stranded", "missing", "collapse", "roof", "rescue", "stairwell"],
    "medical": ["medical", "injured", "insulin", "oxygen", "clinic", "hospital", "pregnant", "bleeding", "dizzy"],
    "water": ["water", "drinking", "dehydrated", "clean water"],
    "shelter": ["shelter", "evacuation", "dry shelter", "over capacity", "housing"],
    "food": ["food", "hungry", "eaten", "meal", "supplies are gone"],
    "power": ["power", "generator", "electricity", "outage", "elevator", "backup power"],
    "transportation": ["transport", "bus", "driver", "route", "road", "underpass", "blocked"],
}

VULNERABILITY_KEYWORDS = {
    "elderly": ["elderly", "senior", "grandmother", "grandfather", "older"],
    "children": ["child", "children", "kids", "infant", "baby"],
    "disabled": ["disabled", "wheelchair", "cannot walk", "mobility"],
    "injured": ["injured", "bleeding", "hurt", "wound"],
    "pregnant": ["pregnant", "contractions"],
    "hospital": ["hospital", "clinic", "patients", "triage"],
}

URGENT_KEYWORDS = {
    "critical": ["trapped", "missing", "cannot breathe", "oxygen", "insulin", "collapse", "roof", "contractions"],
    "high": ["injured", "elderly", "children", "disabled", "flooded", "no power", "no water", "over capacity"],
    "medium": ["shelter", "food", "transport", "blocked", "supplies"],
}

LOW_SEVERITY_URGENCY_PHRASES = (
    "minor injuries",
    "minor injury",
    "stable",
    "non urgent",
    "non-urgent",
    "not urgent",
    "routine",
    "supplies request",
    "extra bandages",
    "medical kits",
    "first-aid station",
    "first aid station",
    "no immediate danger",
)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

NUMBER_TOKEN_PATTERN = (
    r"\d{1,3}|"
    r"twenty[- ](?:one|two|three|four|five|six|seven|eight|nine)|"
    r"thirty[- ](?:one|two|three|four|five|six|seven|eight|nine)|"
    r"forty[- ](?:one|two|three|four|five|six|seven|eight|nine)|"
    r"fifty[- ](?:one|two|three|four|five|six|seven|eight|nine)|"
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|dozen"
)

POPULATION_NOUNS = (
    "people",
    "person",
    "persons",
    "residents",
    "resident",
    "families",
    "family",
    "patients",
    "patient",
    "children",
    "kids",
    "evacuees",
    "crowd",
    "shelter",
    "households",
    "household",
)

INJURY_ONLY_NOUNS = ("injured", "injury", "injuries", "wounded", "hurt")


class NumberCandidate(NamedTuple):
    value: int
    confidence: int
    phrase: str
    family_multiplier: bool = False


CLASSIFICATION_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "resqnet_report_classification",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "need_type": {
                "type": "string",
                "enum": ["medical", "food", "water", "shelter", "rescue", "power", "transportation", "other"],
            },
            "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "people_affected": {"type": "integer", "minimum": 0},
            "vulnerability_indicators": {"type": "array", "items": {"type": "string"}},
            "location_hint": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": [
            "need_type",
            "urgency",
            "people_affected",
            "vulnerability_indicators",
            "location_hint",
            "summary",
        ],
    },
}


def classify_report(report_text: str, *, use_ai: bool = True) -> dict[str, Any]:
    if use_ai and settings.openai_api_key:
        try:
            return _classify_with_openai(report_text)
        except Exception:
            pass
    return _classify_deterministic(report_text)


def _classify_with_openai(report_text: str) -> dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("OpenAI package is not installed")
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=(
            "Classify an emergency report for a crisis-response command center. "
            "Use only facts supported by the report. Keep summary under 24 words."
        ),
        input=report_text,
        text={"format": CLASSIFICATION_SCHEMA},
    )
    return _normalize(json.loads(response.output_text), report_text)


def _classify_deterministic(report_text: str) -> dict[str, Any]:
    text = report_text.lower()
    need_type = _first_matching_need(text)
    urgency = _infer_urgency(text, need_type)
    indicators = _find_vulnerabilities(text)
    people_affected = _infer_people_affected(text, indicators)
    location_hint = _infer_location_hint(report_text)
    summary = _summarize(report_text, need_type, urgency)
    return _normalize(
        {
            "need_type": need_type,
            "urgency": urgency,
            "people_affected": people_affected,
            "vulnerability_indicators": indicators,
            "location_hint": location_hint,
            "summary": summary,
        },
        report_text,
    )


def _first_matching_need(text: str) -> str:
    best_need = "other"
    best_count = 0
    for need_type, keywords in NEED_KEYWORDS.items():
        count = sum(1 for keyword in keywords if keyword in text)
        if count > best_count:
            best_need = need_type
            best_count = count
    return best_need


def _infer_urgency(text: str, need_type: str) -> str:
    for urgency in ("critical", "high", "medium"):
        if any(keyword in text for keyword in URGENT_KEYWORDS[urgency]):
            return urgency
    if need_type == "medical" and any(phrase in text for phrase in LOW_SEVERITY_URGENCY_PHRASES):
        return "medium"
    if need_type in {"rescue", "medical"}:
        return "high"
    if need_type in {"water", "shelter", "food", "power", "transportation"}:
        return "medium"
    return "low"


def _find_vulnerabilities(text: str) -> list[str]:
    found = []
    for indicator, keywords in VULNERABILITY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(indicator)
    return found


def _infer_people_affected(text: str, indicators: list[str]) -> int:
    candidates = _extract_number_candidates(text)
    if candidates:
        best = max(candidates, key=lambda item: (item.confidence, item.value))
        return max(1, min(999, best.value))

    if "dozens of people" in text or "dozens of residents" in text:
        return 24
    if "hundreds of people" in text or "hundreds of residents" in text:
        return 100
    if "elderly couple" in text or "older couple" in text or "senior couple" in text:
        return 2
    if "several residents" in text or "several people" in text or "several families" in text:
        return 6
    if "many people" in text or "many residents" in text:
        return 10
    if "families" in text or "residents" in text or "shelter" in text:
        return 12
    if indicators:
        return 2
    return 1


def _extract_number_candidates(text: str) -> list[NumberCandidate]:
    candidates: list[NumberCandidate] = []
    number_pattern = rf"(?P<number>{NUMBER_TOKEN_PATTERN})"

    for match in re.finditer(rf"\b(?:about|approximately|around|nearly|roughly)?\s*{number_pattern}\s+(?P<noun>[a-z]+)\b", text):
        value = _number_word_to_int(match.group("number"))
        if value is None:
            continue
        noun = match.group("noun")
        phrase = match.group(0).strip()
        if noun in POPULATION_NOUNS:
            multiplier = noun in {"families", "family", "households", "household"}
            candidates.append(NumberCandidate(_apply_family_multiplier(value, multiplier), 90, phrase, multiplier))
        elif noun in INJURY_ONLY_NOUNS:
            candidates.append(NumberCandidate(value, 30, phrase))
        else:
            candidates.append(NumberCandidate(value, 45, phrase))

    for match in re.finditer(rf"\b(?:family|group|household|team)\s+of\s+{number_pattern}\b", text):
        value = _number_word_to_int(match.group("number"))
        if value is not None:
            candidates.append(NumberCandidate(value, 95, match.group(0).strip()))

    for match in re.finditer(rf"\b{number_pattern}\s+(?:families|households)\b", text):
        value = _number_word_to_int(match.group("number"))
        if value is not None:
            candidates.append(NumberCandidate(_apply_family_multiplier(value, True), 92, match.group(0).strip(), True))

    for match in re.finditer(rf"\b{number_pattern}\b", text):
        value = _number_word_to_int(match.group("number"))
        if value is not None:
            candidates.append(NumberCandidate(value, 20, match.group(0).strip()))

    return candidates


def _number_word_to_int(value: str) -> int | None:
    value = value.lower().strip()
    if value.isdigit():
        return int(value)
    if value in {"dozen", "a dozen"}:
        return 12
    if value in NUMBER_WORDS:
        return NUMBER_WORDS[value]
    parts = re.split(r"[-\s]+", value)
    total = 0
    for part in parts:
        if part not in NUMBER_WORDS:
            return None
        total += NUMBER_WORDS[part]
    return total or None


def _apply_family_multiplier(value: int, should_multiply: bool) -> int:
    return value * 4 if should_multiply and value <= 20 else value


def _infer_location_hint(report_text: str) -> str:
    patterns = [
        r"\bat (?:the )?([A-Z][A-Za-z0-9 '\-]+)",
        r"\bnear (?:the )?([A-Z][A-Za-z0-9 '\-]+)",
        r"\bin (?:the )?([A-Z][A-Za-z0-9 '\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, report_text)
        if match:
            hint = re.split(
                r"\s+(?:after|because|with|where|while|and|but|near|at|in)\b",
                match.group(1).strip(),
                maxsplit=1,
            )[0]
            return hint.strip(" .,")
    return ""


def _summarize(report_text: str, need_type: str, urgency: str) -> str:
    clean = " ".join(report_text.strip().split())
    if len(clean) > 140:
        clean = clean[:137].rstrip() + "..."
    return f"{urgency.title()} {need_type} report: {clean}"


def _normalize(result: dict[str, Any], report_text: str) -> dict[str, Any]:
    valid_need_types = {"medical", "food", "water", "shelter", "rescue", "power", "transportation", "other"}
    valid_urgencies = {"low", "medium", "high", "critical"}
    need_type = result.get("need_type") if result.get("need_type") in valid_need_types else "other"
    urgency = result.get("urgency") if result.get("urgency") in valid_urgencies else "low"
    indicators = result.get("vulnerability_indicators") or []
    indicators = [str(item).lower() for item in indicators if str(item).strip()]
    people_affected = int(result.get("people_affected") or 1)
    return {
        "need_type": need_type,
        "urgency": urgency,
        "people_affected": max(1, people_affected),
        "vulnerability_indicators": sorted(set(indicators)),
        "location_hint": str(result.get("location_hint") or ""),
        "summary": str(result.get("summary") or _summarize(report_text, need_type, urgency)),
    }

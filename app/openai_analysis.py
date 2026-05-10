import json
from typing import Any

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from app.settings import settings


client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key and OpenAI else None


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "crisis_call_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "caller_summary": {"type": "string"},
            "need_type": {
                "type": "string",
                "enum": [
                    "medical",
                    "food",
                    "water",
                    "shelter",
                    "rescue",
                    "power",
                    "transportation",
                    "other",
                ],
            },
            "urgency": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
            },
            "vulnerability_indicators": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommended_resource": {"type": "string"},
            "location_hint": {"type": "string"},
            "people_affected": {"type": "integer"},
            "priority_score": {"type": "number", "minimum": 0, "maximum": 1},
            "follow_up_questions": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "caller_summary",
            "need_type",
            "urgency",
            "vulnerability_indicators",
            "recommended_resource",
            "location_hint",
            "people_affected",
            "priority_score",
            "follow_up_questions",
        ],
    },
}


def analyze_transcript(transcript_text: str) -> dict[str, Any] | None:
    if not client:
        return _fallback_analysis(transcript_text)

    try:
        response = client.responses.create(
            model=settings.openai_model,
            instructions=(
                "You analyze emergency call transcripts for ResQNet AI. "
                "Extract only information supported by the transcript. "
                "If a field is unknown, use a cautious value such as 'other', an empty string, "
                "or 0 people affected. Priority score must reflect urgency and vulnerability."
            ),
            input=transcript_text,
            text={"format": ANALYSIS_SCHEMA},
        )
        return json.loads(response.output_text)
    except Exception:
        return _fallback_analysis(transcript_text)


def _fallback_analysis(transcript_text: str) -> dict[str, Any]:
    from app.classifier import classify_report
    from app.scoring import score_incident

    classification = classify_report(transcript_text, use_ai=False)
    score = score_incident(
        report_text=transcript_text,
        need_type=classification["need_type"],
        urgency=classification["urgency"],
        people_affected=classification["people_affected"],
        vulnerability_indicators=classification["vulnerability_indicators"],
    )
    return {
        "caller_summary": classification["summary"],
        "need_type": classification["need_type"],
        "urgency": classification["urgency"],
        "vulnerability_indicators": classification["vulnerability_indicators"],
        "recommended_resource": _recommended_resource(classification["need_type"]),
        "location_hint": classification["location_hint"],
        "people_affected": classification["people_affected"],
        "priority_score": round(score["priority_score"] / 100, 2),
        "follow_up_questions": [
            "What is the exact address or nearest intersection?",
            "Is anyone in immediate medical danger?",
            "Are roads blocked near the location?",
        ],
    }


def _recommended_resource(need_type: str) -> str:
    return {
        "medical": "ambulance or medical team",
        "food": "food truck",
        "water": "water supply unit",
        "shelter": "shelter bus",
        "rescue": "rescue team",
        "power": "power team",
        "transportation": "shelter bus or rescue team",
    }.get(need_type, "field assessment team")

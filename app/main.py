from contextlib import asynccontextmanager
import hashlib
import hmac
import json
from typing import Literal

try:
    from elevenlabs.client import ElevenLabs
except ModuleNotFoundError:
    ElevenLabs = None
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.critical_info import process_conversation, process_unprocessed_conversations
from app.decision_records import sync_missing_decision_records
from app.classifier import classify_report
from app.db import (
    create_incident,
    create_resource,
    get_conversation,
    get_incident,
    get_voice_decision,
    init_db,
    list_assignments,
    list_conversations,
    list_critical_info,
    list_incidents,
    list_resources,
    list_voice_decisions,
    seed_demo_data,
    update_incident_status,
    update_voice_decision_status,
)
from app.elevenlabs_payload import extract_call_fields
from app.ibm_alignment import ibm_alignment_payload
from app.optimizer import optimize_response
from app.planner import generate_response_plan
from app.scoring import risk_tier, score_incident
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ResQNet AI Crisis Response Intelligence System",
    description="Hackathon MVP for emergency report intake, priority scoring, optimization, and response planning.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Static dashboard (HTML/CSS/JS) -----
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "static" / "dashboard"
if DASHBOARD_DIR.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(DASHBOARD_DIR), html=True),
        name="dashboard",
    )

    @app.get("/", include_in_schema=False)
    def _root_redirect():
        return RedirectResponse(url="/dashboard/")

elevenlabs = ElevenLabs(api_key=settings.elevenlabs_api_key or "unused") if ElevenLabs else None


class IncidentCreate(BaseModel):
    report_text: str = Field(min_length=3)
    source: Literal["voice", "sms", "web", "simulated"] = "web"
    location_name: str = "Location pending"
    latitude: float = 43.6532
    longitude: float = -79.3832


class ResourceCreate(BaseModel):
    name: str = Field(min_length=2)
    resource_type: Literal[
        "ambulance",
        "rescue_team",
        "food_truck",
        "water_supply",
        "shelter_bus",
        "power_team",
        "medical_team",
    ]
    capacity: int = Field(default=1, ge=1)
    current_latitude: float = 43.6532
    current_longitude: float = -79.3832
    available: bool = True


class StatusUpdate(BaseModel):
    status: Literal["new", "assigned", "in_progress", "resolved"]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/elevenlabs/post-call")
async def elevenlabs_post_call_webhook(request: Request):
    if not settings.elevenlabs_webhook_secret:
        raise HTTPException(status_code=500, detail="ElevenLabs webhook is not configured")

    raw_body = await request.body()
    signature = request.headers.get("elevenlabs-signature")

    event = construct_elevenlabs_event(raw_body=raw_body, signature=signature)
    if event is None:
        return JSONResponse(content={"error": "Invalid signature"}, status_code=401)

    if event.get("type") != "post_call_transcription":
        return {"status": "ignored", "event_type": event.get("type")}

    fields = extract_call_fields(event)
    transcript_text = fields["transcript_text"] or _fallback_transcript_text(event)

    conversation_id = save_voice_conversation(fields, transcript_text, event, analysis=None)
    saved_conversation = get_conversation(conversation_id)
    enrichment_errors: list[str] = []

    critical_info_id = None
    voice_decision = None
    if saved_conversation:
        try:
            process_result = process_conversation(saved_conversation)
            critical_info_id = process_result["critical_info_id"]
            voice_decision = (
                get_voice_decision(process_result["voice_decision_id"])
                if process_result.get("voice_decision_id")
                else None
            )
        except Exception as exc:
            enrichment_errors.append(f"critical_info: {exc}")

    return {
        "status": "saved",
        "conversation_id": conversation_id,
        "critical_info_id": critical_info_id,
        "voice_decision": voice_decision,
        "enrichment_errors": enrichment_errors,
    }


@app.get("/conversations")
def conversations(limit: int = Query(default=25, ge=1, le=100)):
    return {"conversations": list_conversations(limit=limit)}


@app.get("/conversations/{conversation_id}")
def conversation(conversation_id: int):
    saved = get_conversation(conversation_id)
    if not saved:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return saved


@app.post("/process-conversations")
def process_conversations(limit: int = Query(default=50, ge=1, le=500)):
    return {
        "conversations": process_unprocessed_conversations(limit=limit),
        "missing_decision_records": sync_missing_decision_records(limit=limit),
    }


@app.get("/critical-info")
def critical_info(limit: int = Query(default=25, ge=1, le=100)):
    return {"critical_info": list_critical_info(limit=limit)}


@app.get("/voice-decisions")
def voice_decisions_list(status: str | None = None, limit: int = Query(default=25, ge=1, le=100)):
    return {"voice_decisions": list_voice_decisions(status=status, limit=limit)}


@app.get("/voice-decisions/{voice_decision_id}")
def voice_decisions_get(voice_decision_id: int):
    decision = get_voice_decision(voice_decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Voice decision not found")
    return decision


@app.patch("/voice-decisions/{voice_decision_id}/status")
def voice_decisions_status(voice_decision_id: int, payload: StatusUpdate):
    decision = update_voice_decision_status(voice_decision_id, payload.status)
    if not decision:
        raise HTTPException(status_code=404, detail="Voice decision not found")
    return decision


@app.post("/incidents")
def incidents_create(payload: IncidentCreate):
    return create_incident_from_report(
        report_text=payload.report_text,
        source=payload.source,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )


@app.get("/incidents")
def incidents_list(status: str | None = None):
    return {"incidents": list_incidents(status=status)}


@app.get("/incidents/{incident_id}")
def incidents_get(incident_id: int):
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.patch("/incidents/{incident_id}/status")
def incidents_status(incident_id: int, payload: StatusUpdate):
    incident = update_incident_status(incident_id, payload.status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/resources")
def resources_list(available: bool | None = None):
    return {"resources": list_resources(available=available)}


@app.post("/resources")
def resources_create(payload: ResourceCreate):
    return create_resource(**payload.model_dump())


@app.get("/assignments")
def assignments_list():
    return {"assignments": list_assignments()}


@app.post("/simulate-crisis")
def simulate_crisis(clear_existing: bool = True):
    return seed_demo_data(clear_existing=clear_existing)


@app.get("/demo-data")
def demo_data():
    incidents = list_incidents()
    resources = list_resources()
    assignments = list_assignments()
    return {
        "incidents": incidents,
        "resources": resources,
        "assignments": assignments,
        "summary_stats": build_metrics(incidents=incidents, resources=resources, assignments=assignments),
    }


@app.post("/optimize-response")
def optimize(
    mode: Literal["greedy", "quantum_inspired"] = "greedy",
    source: Literal["auto", "voice", "demo"] = "auto",
):
    return optimize_response(mode=mode, source=source)


@app.post("/generate-plan")
def response_plan(source: Literal["auto", "voice", "demo"] = "auto"):
    return generate_response_plan(source=source)


@app.get("/metrics")
def metrics(source: Literal["auto", "voice", "demo"] = "auto"):
    voice_decisions = list_voice_decisions()
    if source == "voice":
        incidents = voice_decisions
    elif source == "demo":
        incidents = list_incidents()
    else:
        incidents = voice_decisions or list_incidents()
    return build_metrics(
        incidents=incidents,
        resources=list_resources(),
        assignments=list_assignments(),
    )


@app.get("/ibm-alignment")
def ibm_alignment():
    return ibm_alignment_payload()


def save_voice_conversation(
    fields: dict,
    transcript_text: str,
    event: dict,
    analysis: dict | None,
) -> int:
    from app.db import save_conversation

    return save_conversation(
        external_conversation_id=fields["external_conversation_id"],
        caller_phone=fields["caller_phone"],
        agent_id=fields["agent_id"],
        started_at=str(fields["started_at"]) if fields["started_at"] else None,
        duration_seconds=fields["duration_seconds"],
        transcript_text=transcript_text,
        raw_payload=event,
        analysis=analysis,
    )


def construct_elevenlabs_event(raw_body: bytes, signature: str | None) -> dict | None:
    if elevenlabs is not None:
        try:
            return elevenlabs.webhooks.construct_event(
                rawBody=raw_body.decode("utf-8"),
                sig_header=signature,
                secret=settings.elevenlabs_webhook_secret,
            )
        except Exception:
            pass

    if not _verify_elevenlabs_signature(raw_body, signature):
        return None
    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _fallback_transcript_text(event: dict) -> str:
    data = event.get("data") or {}
    analysis = data.get("analysis") or {}
    summary = analysis.get("transcript_summary") or analysis.get("call_summary_title")
    if summary:
        return str(summary)
    return json.dumps(event)


def _verify_elevenlabs_signature(body: bytes, signature_header: str | None) -> bool:
    secret = settings.elevenlabs_webhook_secret
    if not secret or not signature_header:
        return False

    timestamp = None
    received_signature = None
    for part in signature_header.split(","):
        part = part.strip()
        if part.startswith("t="):
            timestamp = part[2:]
        if part.startswith("v0="):
            received_signature = part

    if not timestamp or not received_signature:
        return False

    digest = hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received_signature, "v0=" + digest)


def create_incident_from_report(
    *,
    report_text: str,
    source: str,
    location_name: str,
    latitude: float,
    longitude: float,
):
    classification = classify_report(report_text, use_ai=False)
    score = score_incident(
        report_text=report_text,
        need_type=classification["need_type"],
        urgency=classification["urgency"],
        people_affected=classification["people_affected"],
        vulnerability_indicators=classification["vulnerability_indicators"],
    )
    return create_incident(
        source=source,
        report_text=report_text,
        need_type=classification["need_type"],
        urgency=classification["urgency"],
        priority_score=score["priority_score"],
        people_affected=classification["people_affected"],
        vulnerability_indicators=classification["vulnerability_indicators"],
        location_name=location_name or classification["location_hint"] or "Location pending",
        latitude=latitude,
        longitude=longitude,
        explanation=score["explanation"],
    )


def build_metrics(
    *,
    incidents: list[dict],
    resources: list[dict],
    assignments: list[dict],
) -> dict:
    tiers = [risk_tier(incident["priority_score"]) for incident in incidents]
    assigned = [incident for incident in incidents if incident["status"] == "assigned"]
    resolved = [incident for incident in incidents if incident["status"] == "resolved"]
    if assignments:
        optimized = int(round(sum(8 + assignment["distance_km"] * 2.2 for assignment in assignments) / len(assignments)))
        manual = max(optimized + 18, int(optimized * 1.45))
        saved = int(round(((manual - optimized) / manual) * 100)) if manual else 0
        average_distance = round(sum(assignment["distance_km"] for assignment in assignments) / len(assignments), 2)
    else:
        optimized = 0
        manual = 0
        saved = 0
        average_distance = 0
    return {
        "incident_count": len(incidents),
        "critical_count": tiers.count("Critical"),
        "high_count": tiers.count("High"),
        "medium_count": tiers.count("Medium"),
        "low_count": tiers.count("Low"),
        "available_resources": sum(1 for resource in resources if resource["available"]),
        "assigned_incidents": len(assigned),
        "resolved_incidents": len(resolved),
        "assignments_generated": len(assignments),
        "average_assignment_distance_km": average_distance,
        "estimated_manual_response_time": manual,
        "estimated_optimized_response_time": optimized,
        "estimated_time_saved_percent": saved,
    }

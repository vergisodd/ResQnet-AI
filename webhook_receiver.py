import base64
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

from app.critical_info import process_conversation
from app.db import init_db, save_conversation
from app.elevenlabs_payload import extract_call_fields


load_dotenv()


def verify_signature(body: bytes, signature_header: str | None) -> bool:
    secret = os.getenv("ELEVENLABS_WEBHOOK_SECRET")
    if not secret or not signature_header:
        return False

    timestamp = None
    received_signature = None
    for part in signature_header.split(","):
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


class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"status": "ok"})
            return
        self._json(404, {"detail": "Not Found"})

    def do_POST(self) -> None:
        if self.path != "/webhooks/elevenlabs/post-call":
            self._json(404, {"detail": "Not Found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        signature = self.headers.get("Elevenlabs-Signature")

        if not verify_signature(body, signature):
            self._json(401, {"error": "Invalid signature"})
            return

        event = json.loads(body.decode("utf-8"))
        if event.get("type") != "post_call_transcription":
            self._json(200, {"status": "ignored", "event_type": event.get("type")})
            return

        fields = extract_call_fields(event)
        transcript_text = fields["transcript_text"]
        if not transcript_text:
            transcript_text = json.dumps(event)

        conversation_id = save_conversation(
            external_conversation_id=fields["external_conversation_id"],
            caller_phone=fields["caller_phone"],
            agent_id=fields["agent_id"],
            started_at=str(fields["started_at"]) if fields["started_at"] else None,
            duration_seconds=fields["duration_seconds"],
            transcript_text=transcript_text,
            raw_payload=event,
            analysis=None,
        )
        process_result = process_conversation(
            {
                "id": conversation_id,
                "external_conversation_id": fields["external_conversation_id"],
                "caller_phone": fields["caller_phone"],
                "agent_id": fields["agent_id"],
                "transcript_text": transcript_text,
                "raw_payload": event,
            }
        )
        self._json(
            200,
            {
                "status": "saved",
                "conversation_id": conversation_id,
                "critical_info_id": process_result["critical_info_id"],
                "voice_decision_id": process_result["voice_decision_id"],
            },
        )

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("WEBHOOK_PORT", "8002"))
    server = HTTPServer(("127.0.0.1", port), WebhookHandler)
    print(f"Webhook receiver running on http://127.0.0.1:{port}")
    server.serve_forever()

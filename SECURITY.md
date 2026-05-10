# Security Policy

## Prototype Scope

ResQNet AI is a hackathon prototype for crisis-response coordination demos. It is not a production emergency system and should not be used for real emergency dispatch, medical triage, or public-safety decision making without a full security, privacy, reliability, and operational review.

## Reporting a Vulnerability

Please report security concerns privately instead of opening a public issue.

- GitHub: contact the repository owner, `vergisodd`
- Include the affected area, reproduction steps, expected impact, and any suggested fix
- Do not include real emergency-call recordings, private caller data, API keys, webhook secrets, or other sensitive material in reports

I will try to acknowledge valid reports as quickly as possible and prioritize fixes that could expose secrets, caller data, webhook payloads, or system integrity.

## Sensitive Data

This project may process voice-call metadata, emergency descriptions, locations, contact details, vulnerability indicators, and webhook payloads during local demos or integrations. Treat all realistic test data as sensitive.

- Use synthetic or anonymized data for demos
- Do not commit `.env`, SQLite databases, logs, recordings, raw webhook payloads, or exported incident data
- Rotate any API key or webhook secret that may have been exposed
- Keep `ELEVENLABS_WEBHOOK_SECRET`, `OPENAI_API_KEY`, and database credentials in environment variables only

## Webhook Safety

The ElevenLabs post-call webhook flow should use signed webhooks in any real integration. Before using this beyond a demo:

- Require webhook signature verification
- Use HTTPS only
- Restrict accepted payload sizes
- Log only non-sensitive operational metadata
- Add rate limits and replay protection
- Store only the fields needed for response planning

## Deployment Notes

For public deployments, add a production review before exposing the API:

- Run behind a trusted reverse proxy with TLS
- Use a managed database with backups and least-privilege credentials
- Add authentication and authorization for operator actions
- Add structured audit logs for incident updates and response decisions
- Review data retention and deletion requirements
- Run dependency and container vulnerability scans

## Emergency Disclaimer

For real emergencies, contact the appropriate local emergency services. ResQNet AI is a demo and decision-support prototype, not an emergency-response authority.

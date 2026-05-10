# ResQNet AI Demo Script

Use this as a 2-3 minute voiceover script for the Devpost demo video.

## 0:00-0:20 — Problem

“During climate emergencies, responders get flooded with messy reports from callers, shelters, clinics, and volunteers. The challenge is not just understanding what happened. The challenge is deciding who needs help first when resources are limited.”

## 0:20-0:40 — Product Pitch

“ResQNet AI is a crisis-response command center. It classifies emergency reports, scores urgency and vulnerability, optimizes scarce resource deployment, and generates an explainable command briefing for coordinators.”

“The demo works locally without paid APIs, using deterministic fallback logic for reliability.”

## 0:40-1:10 — Run Judge Demo

Action: click **Run Full Judge Demo**.

Say:

“I’ll run the judge demo. In one action, ResQNet AI generates a Toronto flood scenario, classifies the reports, scores priority, optimizes deployment, and prepares a command briefing.”

Point out:

- Reports analyzed, critical cases, units deployed, unassigned cases, and response-time savings.
- Live Crisis Map.
- Top Critical Incidents.
- Mission Timeline showing completed stages.

## 1:10-1:40 — Optimize Response

Action: point to the optimized deployment results already produced by the judge-demo run.

Say:

“Now ResQNet AI assigns resources. It evaluates priority score, resource suitability, distance, and capacity fit. Each resource can only be assigned once, and unsuitable resource types are excluded.”

Point out:

- Demo Outcome cards.
- Critical incidents assigned.
- Total deployments.
- Average assignment distance.
- Estimated response-time savings.
- Score breakdowns in Resource Deployment cards.

## 1:40-2:10 — Command Briefing

Action: scroll to the **Command Briefing**.

Say:

“The system generates a coordinator-ready command briefing: situation summary, top priorities, deployment plan, risks, communication plan, and SDG alignment.”

“The important part is explainability. A judge can see what the system recommends and why.”

## 2:10-2:35 — Architecture / IBM Alignment

Say:

“Technically, the architecture is modular. Reports enter through voice, manual, or simulated channels. FastAPI normalizes intake. The classifier extracts structured fields. The scoring engine prioritizes incidents. SQLite stores the demo state. The optimizer builds assignments, and FastAPI serves the HTML command dashboard.”

“The current optimizer is classical and explainable. The assignment matrix is a natural extension path for future Qiskit-style constrained optimization. Future versions could also use watsonx or Granite for summarization and command briefing, and IBM Cloud or OpenShift for deployment.”

## 2:35-3:00 — Impact / SDGs / Closing

Say:

“ResQNet AI supports SDG 3 by prioritizing health and vulnerable people, SDG 11 by helping communities coordinate emergency response, and SDG 13 by improving response to climate-driven disasters.”

Close with:

“Most disaster tools tell responders what happened. ResQNet AI tells them what to do next, who to help first, and why.”

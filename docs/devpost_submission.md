# Devpost Submission Draft

## Project Title

ResQNet AI

## Source Code

https://github.com/OmidRahmanian/ResQnet

## Elevator Pitch

ResQNet AI is a crisis-response command center that converts emergency reports into prioritized, explainable resource-allocation decisions for climate disasters.

## Inspiration

Climate emergencies are becoming more frequent and more complex. During a flood, heatwave, storm, or power outage, responders do not only need a map of what happened. They need to decide what to do first when people are vulnerable and resources are limited.

We built ResQNet AI to support that decision moment: who needs help first, which resource should respond, and why that recommendation is fair and explainable.

## What It Does

ResQNet AI:

- Accepts voice, manual, and simulated crisis reports.
- Classifies each report by need type, urgency, people affected, and vulnerability indicators.
- Scores every incident from 0-100 with a readable explanation.
- Escalates mass-care emergencies such as food, water, and shelter shortages affecting many people.
- Moderates low-severity supply requests so minor incidents do not overwhelm life-safety cases.
- Shows incidents and resources on a bright crisis command dashboard.
- Optimizes resource assignments using priority, suitability, distance, and capacity.
- Explains every deployment with score breakdowns.
- Generates a coordinator-ready command briefing for emergency coordinators.
- Works without paid APIs by using deterministic fallback logic.

## Demo Result

The built-in Toronto flood simulation currently creates:

- 14 simulated emergency reports.
- 10 response resources.
- 10 optimized assignments.
- About 55% estimated response-time savings versus a simple manual allocation baseline.
- Unassigned-incident reasons when resources run out.

These results come from local simulated data and the classical optimizer in this repository.

## How We Built It

We built a Python FastAPI backend with SQLite-first persistence and Postgres-compatible helper logic. The original Phase 1 voice-intake path uses ElevenLabs post-call webhooks and optional OpenAI structured analysis when credentials are available. For demo reliability, we added deterministic classification and planning fallbacks so the product works without paid APIs.

The optimizer is a transparent greedy assignment engine. It sorts unresolved incidents by priority, evaluates operationally suitable resources, scores resource match, priority weight, distance penalty, and capacity fit, then creates deployment assignments. Each assignment returns a score breakdown so judges can inspect why the decision happened.

The dashboard is built with HTML, CSS, vanilla JavaScript, and Leaflet, served directly by FastAPI. The main presentation path is **Run Full Judge Demo**, which generates the scenario, optimizes response allocation, renders the command briefing, and updates the mission timeline in one flow.

## IBM Alignment

The current prototype is classical and local. It does not claim real quantum advantage or live IBM deployment.

The IBM extension path is credible:

- The incident-resource assignment matrix maps naturally to constrained optimization.
- A future version could encode the assignment problem as a QUBO or Ising-style model for a Qiskit demonstration.
- Future briefing and multilingual summarization could use IBM watsonx.ai or Granite.
- A resilient production architecture could use IBM Z or LinuxONE concepts for secure, high-availability crisis transaction processing.
- The backend, optimizer, and dashboard could be containerized for Red Hat OpenShift or IBM Cloud.

## Challenges We Ran Into

- Making the demo reliable without paid APIs.
- Extracting people counts correctly from messy emergency language.
- Balancing mass-care emergencies against individual life-safety incidents.
- Keeping optimization explainable rather than black-box.
- Presenting IBM and quantum alignment honestly without overstating what the prototype does today.

## Accomplishments We Are Proud Of

- Built an end-to-end crisis-response command-center prototype.
- Preserved the voice webhook architecture while adding a full demo workflow.
- Improved classification for families, residents, patients, and number-word counts.
- Added mass-care priority escalation and low-severity dampening.
- Added optimizer score breakdowns and unassigned-incident reasons.
- Built a polished command-center dashboard that tells the story in one judge-demo click.
- Added tests for classifier, scoring, optimizer, API flow, and dashboard syntax.

## What We Learned

Disaster response is a decision problem, not just a data problem. A useful AI system in this space must be reliable, transparent, and human-centered. We also learned that explainability is not optional: coordinators need to understand why a recommendation was made before they can trust it.

## What Is Next For ResQNet AI

- Add live SMS or WhatsApp intake.
- Integrate real weather, road-closure, shelter, clinic, and flood data.
- Replace straight-line distance with route-aware travel time.
- Explore a small Qiskit assignment demo.
- Evaluate watsonx.ai or Granite for multilingual summarization and command briefings.
- Containerize the services for an IBM Cloud or OpenShift deployment path.

## Built With

- Python
- FastAPI
- HTML / CSS / vanilla JavaScript
- Leaflet
- SQLite
- Postgres-compatible SQL
- Deterministic classification fallback
- Optional OpenAI structured outputs
- ElevenLabs webhook architecture
- pytest

## UN SDG Alignment

### SDG 3: Good Health and Well-Being

ResQNet AI prioritizes medical emergencies, patients with medication or oxygen needs, and vulnerable residents during a crisis.

### SDG 11: Sustainable Cities and Communities

The system supports city-level emergency coordination, shelter response, transport support, and aid distribution.

### SDG 13: Climate Action

The demo focuses on climate-driven emergencies such as floods, storms, power outages, and resource shortages.

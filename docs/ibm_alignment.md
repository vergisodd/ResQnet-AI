# IBM Alignment

ResQNet AI is a hackathon prototype with a classical, explainable implementation today and a credible extension path toward IBM AI, optimization, and resilient infrastructure workflows.

## Current Implementation

The current system runs locally with:

- FastAPI crisis-intake API.
- SQLite-first persistence with Postgres-compatible helpers.
- Deterministic report classification that works without paid APIs.
- Optional OpenAI-based structured analysis when credentials are available.
- Priority scoring with vulnerability, urgency, mass-care, and severity-dampening logic.
- A classical greedy optimizer that assigns available resources to high-priority incidents.
- A FastAPI-served HTML/CSS/JavaScript dashboard for simulation, optimization, and command briefing.

## Why Crisis Response Is An Optimization Problem

During a disaster, coordinators must decide which limited resource should respond to which incident. Each incident has different urgency, vulnerability, location, people affected, and operational need. Each resource has different type, capacity, availability, and location.

That creates an assignment problem:

- Rows: active incidents.
- Columns: available response resources.
- Score: priority plus resource suitability minus travel penalty plus capacity fit.
- Decision: choose the highest-value feasible assignments.

## Objective Function

The current optimizer approximates this objective:

```text
maximize:
  incident priority
+ resource suitability
+ capacity fit
- distance penalty
```

The implementation is intentionally transparent so judges and responders can inspect why each assignment was made.

## Constraints

The prototype enforces practical constraints:

- A resource can be assigned to at most one incident per dispatch cycle.
- A resource type must match the operational need.
- Critical incidents are evaluated before lower-priority incidents.
- Assigned resources become unavailable for later assignments.
- Incidents without suitable remaining resources are returned with an unassigned reason.

## Quantum-Inspired Extension Path

The current version does not use Qiskit and does not claim quantum advantage.

The assignment matrix could be encoded later as a QUBO or Ising-style problem:

- Binary variable: assign resource `r` to incident `i`.
- Objective: maximize priority-weighted response value.
- Penalties: duplicate resource assignment, unsuitable resource type, excessive distance, unserved critical incidents.

That makes ResQNet AI a good candidate for a future Qiskit demonstration, while keeping the hackathon demo reliable with a classical optimizer today.

## watsonx / Granite Future Path

Future versions could replace or augment optional OpenAI calls with IBM watsonx.ai or Granite models for:

- Multilingual emergency-report summarization.
- Safer structured extraction from messy voice transcripts.
- Command-briefing generation.
- Translation between public-facing and responder-facing crisis communication.

## IBM Z / LinuxONE Future Path

Emergency coordination systems need resilience, auditability, and secure transaction processing. A future production architecture could use IBM Z or LinuxONE concepts for:

- High-availability incident intake.
- Secure crisis-event transaction logs.
- Reliable routing of resource-assignment decisions.
- Operational continuity during severe public emergencies.

## Red Hat OpenShift / IBM Cloud Future Path

The current FastAPI backend, dashboard, and data services could become containerized crisis microservices deployed on Red Hat OpenShift or IBM Cloud:

- Intake service.
- Classification service.
- Optimization service.
- Command-briefing service.
- Dashboard service.
- Managed database.

## Honesty Statement

This hackathon prototype does not claim real quantum advantage, real IBM production deployment, or real emergency-agency usage. It demonstrates a technically credible, modular path toward IBM AI, optimization, and resilient infrastructure workflows.

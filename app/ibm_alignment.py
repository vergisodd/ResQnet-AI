from __future__ import annotations


def ibm_alignment_payload() -> dict:
    return {
        "current_mode": (
            "Hackathon prototype using deterministic classification, transparent priority scoring, "
            "SQLite-first persistence, and a classical explainable greedy optimizer."
        ),
        "optimization_model": {
            "decision": "Assign available response resources to active incidents.",
            "objective": (
                "Maximize incident priority plus resource suitability and capacity fit, "
                "while minimizing distance penalty and leaving explanations for every assignment."
            ),
            "constraints": [
                "A resource can be assigned to at most one incident in the current dispatch cycle.",
                "Resource type must be operationally suitable for the incident need.",
                "Critical incidents are evaluated before lower-priority incidents.",
                "Unavailable or already assigned resources are excluded from later assignments.",
            ],
        },
        "ibm_extension_paths": {
            "qiskit": (
                "The incident-resource assignment matrix could be encoded as a QUBO or Ising-style "
                "optimization problem for a future Qiskit demonstration. The current repo does not "
                "claim quantum advantage."
            ),
            "watsonx_granite": (
                "Future versions could use watsonx.ai or Granite for report summarization, "
                "multilingual intake, and command-briefing generation."
            ),
            "ibm_z_linuxone": (
                "A production architecture could use IBM Z or LinuxONE for secure, resilient, "
                "high-availability crisis transaction processing."
            ),
            "openshift_ibm_cloud": (
                "The FastAPI, dashboard, and data services could be containerized and deployed "
                "as scalable crisis-response microservices on Red Hat OpenShift or IBM Cloud."
            ),
        },
        "honesty_statement": (
            "This hackathon prototype does not claim real quantum advantage, live IBM deployment, "
            "or production emergency-agency use. It demonstrates a credible architecture and "
            "extension path for IBM AI, optimization, and resilient infrastructure workflows."
        ),
    }

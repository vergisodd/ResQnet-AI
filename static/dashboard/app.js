const API = (() => {
  const origin = window.location.origin;
  if (origin && !origin.startsWith("file:") && !origin.includes(":5500")) return origin;
  return "http://127.0.0.1:8000";
})();

const state = {
  online: null,
  metrics: {},
  incidents: [],
  resources: [],
  assignments: [],
  briefing: null,
  ibm: null,
  source: "demo",
  activeFilter: "all",
  map: null,
  tileLayer: null,
  tileWarningShown: false,
  layers: { incidents: null, resources: null, lines: null },
  prevKpi: {},
};

const q = (selector) => document.querySelector(selector);
const qa = (selector) => [...document.querySelectorAll(selector)];

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`${response.status} ${response.statusText}${body ? `: ${body}` : ""}`);
  }
  return response.json();
}

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function formatNeed(value) {
  return escapeHtml(String(value || "unknown").replace(/_/g, " "));
}

function formatNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString() : fallback.toLocaleString();
}

function formatDistance(value) {
  const numeric = Number(value || 0);
  return `${numeric.toFixed(2)} km`;
}

function riskTier(score) {
  if (score >= 80) return "Critical";
  if (score >= 60) return "High";
  if (score >= 40) return "Medium";
  return "Low";
}

function incidentTier(incident) {
  return incident.risk_tier || riskTier(Number(incident.priority_score || 0));
}

function truncate(text, max = 150) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return clean.slice(0, max - 1).trimEnd() + "...";
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function toast(message, type = "info") {
  const stack = document.getElementById("toast-stack");
  const el = document.createElement("div");
  const icon = type === "success" ? "OK" : type === "error" ? "!" : "i";
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="t-icon">${icon}</span><span class="t-msg">${escapeHtml(message)}</span>`;
  stack.appendChild(el);
  setTimeout(() => {
    el.style.transition = "opacity 0.25s ease, transform 0.25s ease";
    el.style.opacity = "0";
    el.style.transform = "translateX(18px)";
    setTimeout(() => el.remove(), 260);
  }, 3800);
}

function setBusy(button, busy) {
  if (!button) return;
  button.classList.toggle("loading", busy);
  button.disabled = busy;
}

function setActionButtons(disabled) {
  ["btn-full-demo", "btn-simulate", "btn-optimize", "btn-plan", "btn-plan-2", "btn-refresh", "btn-source-demo", "btn-source-voice"].forEach((id) => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = disabled;
  });
}

async function withButton(button, task) {
  setBusy(button, true);
  try {
    return await task();
  } finally {
    setBusy(button, false);
  }
}

async function checkHealth() {
  const pill = document.getElementById("backend-pill");
  const down = document.getElementById("backend-down");
  try {
    await api("/health");
    pill.className = "status-pill status-online";
    pill.innerHTML = '<span class="dot"></span>Backend online';
    down.classList.add("hidden");
    state.online = true;
    return true;
  } catch {
    pill.className = "status-pill status-offline";
    pill.innerHTML = '<span class="dot"></span>Backend offline';
    down.classList.remove("hidden");
    state.online = false;
    return false;
  }
}

function animateValue(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const numeric = Number(target || 0);
  const from = state.prevKpi[id] ?? 0;
  const start = performance.now();
  const duration = 650;

  function tick(now) {
    const progress = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(from + (numeric - from) * eased);
    el.textContent = value.toLocaleString();
    if (progress < 1) requestAnimationFrame(tick);
    else {
      el.textContent = Math.round(numeric).toLocaleString();
      state.prevKpi[id] = numeric;
    }
  }
  requestAnimationFrame(tick);
}

function unassignedCount(metrics = state.metrics, incidents = state.incidents, assignments = state.assignments) {
  if (metrics.unassigned_incidents_count !== undefined) return Number(metrics.unassigned_incidents_count);
  const assignedIds = new Set(assignments.map(assignmentTargetId).filter(Boolean));
  return incidents.filter((incident) => incident.status !== "resolved" && !assignedIds.has(incident.id)).length;
}

function assignmentTargetId(assignment) {
  return state.source === "voice" ? assignment.voice_decision_id : assignment.incident_id;
}

function renderOutcome() {
  const metrics = state.metrics || {};
  const incidents = state.incidents || [];
  const assignments = state.assignments || [];
  const averageDistance = metrics.average_assignment_distance_km || (
    assignments.length
      ? assignments.reduce((total, assignment) => total + Number(assignment.distance_km || 0), 0) / assignments.length
      : 0
  );

  animateValue("outcome-reports", metrics.incident_count ?? incidents.length);
  animateValue("outcome-critical", metrics.critical_count ?? incidents.filter((incident) => incidentTier(incident) === "Critical").length);
  animateValue("outcome-deployed", metrics.assignments_generated ?? assignments.length);
  animateValue("outcome-unassigned", unassignedCount(metrics, incidents, assignments));
  animateValue("outcome-saved", metrics.estimated_time_saved_percent ?? 0);

  const help = assignments.length
    ? `Avg deployment distance ${Number(averageDistance || 0).toFixed(2)} km`
    : state.source === "voice" ? "Optimize voice calls to generate deployments." : "Run the judge demo to generate the live scenario.";
  setText("outcome-distance", help);
  setText("active-source-label", state.source === "voice" ? "Voice Calls" : "Demo Ops");
}

function timelineSteps() {
  const hasIncidents = state.incidents.length > 0;
  const hasScores = hasIncidents && state.incidents.every((incident) => Number.isFinite(Number(incident.priority_score)));
  const hasAssignments = state.assignments.length > 0;
  const hasBriefing = Boolean(state.briefing);
  return [
    { title: state.source === "voice" ? "Voice decisions loaded" : "Crisis generated", detail: "Reports loaded from the backend", complete: hasIncidents },
    { title: "Reports structured", detail: "Need, urgency, people, and vulnerability extracted", complete: hasIncidents },
    { title: "Priorities scored", detail: "Reports ranked from Low to Critical", complete: hasScores },
    { title: "Resources optimized", detail: "Units matched to highest-risk incidents", complete: hasAssignments },
    { title: "Briefing generated", detail: "Coordinator-ready response plan prepared", complete: hasBriefing },
  ];
}

function renderTimeline() {
  const root = document.getElementById("timeline");
  const steps = timelineSteps();
  const activeIndex = steps.findIndex((step) => !step.complete);
  root.innerHTML = steps.map((step, index) => {
    const status = step.complete ? "Complete" : index === activeIndex ? "Active" : "Pending";
    const cls = step.complete ? "complete" : index === activeIndex ? "active" : "pending";
    return `
      <div class="timeline-step ${cls}">
        <div class="timeline-dot">${index + 1}</div>
        <div>
          <div class="timeline-title">${escapeHtml(step.title)}</div>
          <div class="timeline-detail">${escapeHtml(step.detail)}</div>
        </div>
        <div class="timeline-status">${status}</div>
      </div>
    `;
  }).join("");
}

function emptyState(title, copy) {
  return `<div class="empty-state"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(copy)}</p></div>`;
}

function renderTopIncidents() {
  const root = document.getElementById("top-incidents");
  const top = [...state.incidents]
    .sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0))
    .slice(0, 3);

  if (!top.length) {
    root.innerHTML = emptyState("No crisis loaded", "Run the judge demo to generate a flood-response scenario.");
    return;
  }

  root.innerHTML = top.map((incident) => {
    const tier = incidentTier(incident);
    return `
      <article class="priority-card ${tier}">
        <div class="priority-top">
          <div class="score-badge">${Math.round(Number(incident.priority_score || 0))}</div>
          <div>
            <div class="priority-title">${escapeHtml(incident.location_name || "Location pending")}</div>
            <div class="priority-meta">${formatNeed(incident.need_type)} / ${formatNumber(incident.people_affected, 1)} affected</div>
          </div>
          <span class="badge badge-${tier}">${tier}</span>
        </div>
        <div class="priority-why">${escapeHtml(truncate(incident.explanation, 132))}</div>
      </article>
    `;
  }).join("");
}

function renderIncidentTable() {
  const tbody = q("#incident-table tbody");
  const assignedIds = new Set(state.assignments.map(assignmentTargetId).filter(Boolean));
  const filtered = filterIncidents(state.incidents, state.activeFilter, assignedIds)
    .sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0));

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="7">${emptyState("No matching reports", "Change the filter or run the judge demo.")}</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((incident) => {
    const tier = incidentTier(incident);
    return `
      <tr>
        <td><span class="table-score">${Math.round(Number(incident.priority_score || 0))}</span></td>
        <td><span class="badge badge-${tier}">${tier}</span></td>
        <td><strong>${escapeHtml(incident.location_name || "Location pending")}</strong></td>
        <td>${formatNeed(incident.need_type)}</td>
        <td>${formatNumber(incident.people_affected, 1)}</td>
        <td><span class="badge badge-${escapeHtml(incident.status || "new")}">${escapeHtml(incident.status || "new").replace(/_/g, " ")}</span></td>
        <td class="explain-cell">${escapeHtml(truncate(incident.explanation, 170))}</td>
      </tr>
    `;
  }).join("");
}

function filterIncidents(incidents, filter, assignedIds) {
  if (filter === "all") return incidents;
  if (filter === "critical") return incidents.filter((incident) => incidentTier(incident) === "Critical");
  if (filter === "high") return incidents.filter((incident) => incidentTier(incident) === "High");
  if (filter === "medical") return incidents.filter((incident) => incident.need_type === "medical");
  if (filter === "rescue") return incidents.filter((incident) => incident.need_type === "rescue");
  if (filter === "mass-care") return incidents.filter((incident) => ["food", "water", "shelter"].includes(incident.need_type));
  if (filter === "unassigned") return incidents.filter((incident) => incident.status !== "resolved" && !assignedIds.has(incident.id));
  return incidents;
}

function renderResources() {
  const root = document.getElementById("resources");
  if (!state.resources.length) {
    root.innerHTML = emptyState("No fleet loaded", "Generate the crisis scenario to provision response units.");
    return;
  }

  root.innerHTML = state.resources.map((resource) => `
    <article class="fleet-card">
      <div class="fleet-icon" aria-hidden="true">${resourceIcon(resource.resource_type)}</div>
      <div>
        <div class="fleet-name">${escapeHtml(resource.name)}</div>
        <div class="fleet-meta">${formatNeed(resource.resource_type)} / <span class="badge badge-${resource.available ? "available" : "assigned"}">${resource.available ? "Available" : "Assigned"}</span></div>
      </div>
      <div class="fleet-capacity"><strong>${formatNumber(resource.capacity, 1)}</strong>capacity</div>
    </article>
  `).join("");
}

function resourceIcon(resourceType) {
  const icons = {
    ambulance: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M3 6h11v5h2.4l2-3H21v9h-2a3 3 0 0 1-6 0H9a3 3 0 0 1-6 0H2V8a2 2 0 0 1 1-2Zm3 12a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm10 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2ZM7 8v2H5v2h2v2h2v-2h2v-2H9V8H7Z"/></svg>',
    rescue_team: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M12 2 3 6v6c0 5.2 3.8 8.8 9 10 5.2-1.2 9-4.8 9-10V6l-9-4Zm-1 5h2v4h4v2h-4v4h-2v-4H7v-2h4V7Z"/></svg>',
    medical_team: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M10 3h4v6h6v4h-6v8h-4v-8H4V9h6V3Z"/></svg>',
    food_truck: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M4 5h10v10h1.5l2-3H21v6h-2.2a2.8 2.8 0 0 1-5.6 0H9.8a2.8 2.8 0 0 1-5.6 0H3V6a1 1 0 0 1 1-1Zm3 14a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm9 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"/></svg>',
    water_supply: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M12 2s7 7.2 7 12a7 7 0 0 1-14 0c0-4.8 7-12 7-12Zm0 17a5 5 0 0 0 5-5c0-2.2-2.5-5.9-5-8.9C9.5 8.1 7 11.8 7 14a5 5 0 0 0 5 5Z"/></svg>',
    shelter_bus: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M6 3h12a3 3 0 0 1 3 3v10a3 3 0 0 1-2 2.8V21h-2v-2H7v2H5v-2.2A3 3 0 0 1 3 16V6a3 3 0 0 1 3-3Zm0 3v5h12V6H6Zm1 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm10 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"/></svg>',
    power_team: '<svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z"/></svg>',
  };
  return icons[resourceType] || icons.rescue_team;
}

function renderAssignments() {
  const root = document.getElementById("assignments");
  if (!state.assignments.length) {
    root.innerHTML = emptyState("No deployments yet", "Run Optimize Response or the full judge demo.");
    return;
  }

  root.innerHTML = state.assignments.map((assignment) => {
    const tier = assignment.incident_risk_tier || riskTier(Number(assignment.incident_priority_score || 0));
    const bd = assignment.score_breakdown || {};
    const breakdown = Object.entries(bd).length ? `
      <details class="score-details">
        <summary>Show score breakdown</summary>
        <div class="breakdown-grid">
          ${Object.entries(bd).map(([key, value]) => `
            <div><strong>${Number.isFinite(Number(value)) ? Number(value).toFixed(2) : escapeHtml(value)}</strong>${escapeHtml(key.replace(/_/g, " "))}</div>
          `).join("")}
        </div>
      </details>
    ` : "";

    return `
      <article class="deployment-card">
        <div class="deployment-flow">
          <div class="deployment-node resource" title="${escapeHtml(assignment.resource_name || "")}">${escapeHtml(assignment.resource_name || "Resource")}</div>
          <div class="deployment-arrow">-&gt;</div>
          <div class="deployment-node incident" title="${escapeHtml(assignment.incident_location || "")}">${escapeHtml(assignment.incident_location || "Incident")}</div>
        </div>
        <div class="deployment-stats">
          <div class="deployment-stat"><strong>${formatNeed(assignment.resource_type)}</strong>resource</div>
          <div class="deployment-stat"><strong>${formatNeed(assignment.incident_need_type)}</strong>need</div>
          <div class="deployment-stat"><strong>${formatDistance(assignment.distance_km)}</strong>distance</div>
          <div class="deployment-stat"><strong>${Number(assignment.suitability_score || 0).toFixed(1)}</strong>suitability</div>
          <div class="deployment-stat"><strong>${Math.round(Number(assignment.incident_priority_score || 0))}</strong>${tier}</div>
        </div>
        <p class="deployment-reason">${escapeHtml(assignment.assignment_reason || "Selected by priority, fit, distance, and capacity.")}</p>
        ${breakdown}
      </article>
    `;
  }).join("");
}

function initMap() {
  if (state.map) return;
  state.map = L.map("map", {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView([43.6532, -79.3832], 12);

  let tileErrors = 0;
  state.tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  })
    .on("tileerror", () => {
      tileErrors += 1;
      if (tileErrors > 3 && !state.tileWarningShown) {
        state.tileWarningShown = true;
        document.getElementById("map").classList.add("tiles-failed");
        toast("Map tiles unavailable; using offline grid fallback with live markers.", "info");
      }
    })
    .addTo(state.map);

  state.layers.lines = L.layerGroup().addTo(state.map);
  state.layers.incidents = L.layerGroup().addTo(state.map);
  state.layers.resources = L.layerGroup().addTo(state.map);
}

function mapIcon(type, size = 18) {
  return L.divIcon({
    className: "",
    html: `<div class="map-pin ${type}"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function renderMap() {
  initMap();
  Object.values(state.layers).forEach((layer) => layer.clearLayers());

  const resourcesById = Object.fromEntries(state.resources.map((resource) => [resource.id, resource]));
  const assignmentsByIncident = {};
  state.assignments.forEach((assignment) => {
    assignmentsByIncident[assignmentTargetId(assignment)] = assignment;
  });

  const bounds = [];

  state.assignments.forEach((assignment) => {
    const resource = resourcesById[assignment.resource_id];
    const incident = state.incidents.find((item) => item.id === assignmentTargetId(assignment));
    if (!resource || !incident) return;
    if (!resource.current_latitude || !incident.latitude) return;
    L.polyline(
      [
        [resource.current_latitude, resource.current_longitude],
        [incident.latitude, incident.longitude],
      ],
      { color: "#00b8d9", weight: 3, opacity: 0.72, dashArray: "7, 7" }
    ).addTo(state.layers.lines);
  });

  state.incidents.forEach((incident) => {
    if (!incident.latitude || !incident.longitude) return;
    const tier = incidentTier(incident);
    const cls = tier.toLowerCase();
    const assignment = assignmentsByIncident[incident.id];
    const popup = `
      <strong>${escapeHtml(incident.location_name || "Incident")}</strong><br>
      ${formatNeed(incident.need_type)} / ${escapeHtml(incident.urgency || "unknown")}<br>
      Priority <strong>${Math.round(Number(incident.priority_score || 0))}</strong> (${tier})<br>
      ${formatNumber(incident.people_affected, 1)} people affected
      ${assignment ? `<br>Assigned: <strong>${escapeHtml(assignment.resource_name)}</strong>` : "<br>Assigned: pending"}
    `;
    L.marker([incident.latitude, incident.longitude], {
      icon: mapIcon(cls, tier === "Critical" ? 26 : tier === "High" ? 22 : 18),
    }).bindPopup(popup).addTo(state.layers.incidents);
    bounds.push([incident.latitude, incident.longitude]);
  });

  state.resources.forEach((resource) => {
    if (!resource.current_latitude || !resource.current_longitude) return;
    const cls = resource.available ? "resource" : "resource busy";
    L.marker([resource.current_latitude, resource.current_longitude], {
      icon: mapIcon(cls, 18),
    }).bindPopup(`
      <strong>${escapeHtml(resource.name)}</strong><br>
      ${formatNeed(resource.resource_type)}<br>
      ${resource.available ? "Available" : "Assigned"} / capacity ${formatNumber(resource.capacity, 1)}
    `).addTo(state.layers.resources);
    bounds.push([resource.current_latitude, resource.current_longitude]);
  });

  if (bounds.length) {
    state.map.fitBounds(bounds, { padding: [42, 42], maxZoom: 13 });
  }
}

function sectionMap() {
  return [
    ["executive_summary", "Situation Summary"],
    ["top_priorities", "Top Priorities"],
    ["resource_assignments", "Deployment Plan"],
    ["risks_and_constraints", "Risks & Constraints"],
    ["communication_plan", "Communication Plan"],
    ["sdg_alignment", "SDG / Humanitarian Impact"],
    ["explainability_notes", "Explainability Notes"],
  ];
}

function renderBriefing(plan) {
  const root = document.getElementById("briefing");
  if (!plan) {
    root.innerHTML = emptyState("No briefing generated", "Run the full judge demo or click Generate Briefing after optimization.");
    setText("briefing-timestamp", "Awaiting briefing");
    state.briefing = null;
    renderTimeline();
    return;
  }

  state.briefing = plan;
  setText("briefing-timestamp", new Date().toLocaleString([], { dateStyle: "medium", timeStyle: "short" }));
  const html = sectionMap().map(([key, title]) => {
    const value = plan[key];
    if (value === undefined || value === null) return "";
    return `<section class="brief-section"><h3>${title}</h3>${renderBriefValue(value)}</section>`;
  }).filter(Boolean).join("");

  root.innerHTML = html || emptyState("Briefing returned empty", "Try generating the plan again.");
  renderTimeline();
}

function renderBriefValue(value) {
  if (Array.isArray(value)) {
    if (!value.length) return "<p>No items reported.</p>";
    return `<ul>${value.map((item) => `<li>${typeof item === "object" ? renderObjectInline(item) : escapeHtml(item)}</li>`).join("")}</ul>`;
  }
  if (typeof value === "object" && value !== null) {
    return `<div class="kv">${Object.entries(value).map(([key, val]) => `
      <div class="kv-row"><strong>${escapeHtml(key.replace(/_/g, " "))}</strong><span>${Array.isArray(val) ? val.map(escapeHtml).join(", ") : escapeHtml(String(val))}</span></div>
    `).join("")}</div>`;
  }
  return `<p>${escapeHtml(value)}</p>`;
}

function renderObjectInline(obj) {
  return Object.entries(obj).map(([key, value]) => {
    const rendered = typeof value === "object" ? escapeHtml(JSON.stringify(value)) : escapeHtml(String(value));
    return `<strong>${escapeHtml(key.replace(/_/g, " "))}:</strong> ${rendered}`;
  }).join(" / ");
}

function briefingMarkdown() {
  if (!state.briefing) return "";
  const lines = ["# ResQNet AI Command Briefing", "", `Generated: ${new Date().toLocaleString()}`, ""];
  sectionMap().forEach(([key, title]) => {
    const value = state.briefing[key];
    if (value === undefined || value === null) return;
    lines.push(`## ${title}`);
    if (Array.isArray(value)) {
      value.forEach((item) => {
        lines.push(`- ${typeof item === "object" ? Object.entries(item).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`).join("; ") : item}`);
      });
    } else if (typeof value === "object") {
      Object.entries(value).forEach(([k, v]) => lines.push(`- ${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`));
    } else {
      lines.push(String(value));
    }
    lines.push("");
  });
  return lines.join("\n");
}

function renderIbm() {
  const root = document.getElementById("ibm-panel");
  const payload = state.ibm;
  if (!payload) {
    root.innerHTML = emptyState("IBM alignment unavailable", "The backend alignment endpoint did not respond.");
    return;
  }
  const paths = payload.ibm_extension_paths || {};
  root.innerHTML = `
    <article class="ibm-card">
      <h3>Explainable Optimizer Today</h3>
      <p>${escapeHtml(payload.current_mode || "Classical transparent scoring and assignment.")}</p>
    </article>
    <article class="ibm-card">
      <h3>Qiskit Extension Path</h3>
      <p>${escapeHtml(paths.qiskit || "Future constrained-assignment optimization candidate.")}</p>
    </article>
    <article class="ibm-card">
      <h3>watsonx / Granite Path</h3>
      <p>${escapeHtml(paths.watsonx_granite || "Future multilingual summarization and briefing generation path.")}</p>
    </article>
    <article class="ibm-card">
      <h3>IBM Z / OpenShift Path</h3>
      <p>${escapeHtml([paths.ibm_z_linuxone, paths.openshift_ibm_cloud].filter(Boolean).join(" "))}</p>
    </article>
    <article class="ibm-card honesty">
      <strong>Honesty line:</strong>
      <span>${escapeHtml(payload.honesty_statement || "This hackathon prototype does not claim production deployment or quantum advantage.")}</span>
    </article>
  `;
}

function renderEverything() {
  renderOutcome();
  renderTimeline();
  renderTopIncidents();
  renderIncidentTable();
  renderResources();
  renderAssignments();
  renderMap();
  renderIbm();
}

async function loadAll() {
  if (!(await checkHealth())) return;
  try {
    const [data, metrics, assignments, resources, ibm] = state.source === "voice"
      ? await Promise.all([
          api("/voice-decisions?limit=100"),
          api("/metrics?source=voice"),
          api("/assignments"),
          api("/resources"),
          api("/ibm-alignment").catch(() => null),
        ])
      : await Promise.all([
          api("/demo-data"),
          api("/metrics?source=demo"),
          null,
          null,
          api("/ibm-alignment").catch(() => null),
        ]);

    if (state.source === "voice") {
      state.incidents = data.voice_decisions || [];
      state.resources = resources.resources || [];
      state.assignments = (assignments.assignments || []).filter((assignment) => assignment.assignment_source === "voice_decision");
      state.metrics = metrics || {};
    } else {
      state.incidents = data.incidents || [];
      state.resources = data.resources || [];
      state.assignments = (data.assignments || []).filter((assignment) => assignment.assignment_source !== "voice_decision");
      state.metrics = metrics || data.summary_stats || {};
    }
    state.ibm = ibm;
    syncSourceButtons();
    renderEverything();
  } catch (error) {
    console.error(error);
    toast(`Dashboard load failed: ${error.message}`, "error");
  }
}

async function runSimulation() {
  setSource("demo", { render: false });
  const result = await api("/simulate-crisis", { method: "POST" });
  state.briefing = null;
  renderBriefing(null);
  await loadAll();
  toast(`Scenario loaded: ${result.incidents_created} reports, ${result.resources_created} resources`, "success");
}

async function runOptimization() {
  const result = await api(`/optimize-response?mode=quantum_inspired&source=${state.source}`, { method: "POST" });
  await loadAll();
  const summary = result.optimization_summary || {};
  toast(`Deployment optimized: ${summary.total_assignments_created ?? result.assignments?.length ?? 0} units assigned`, "success");
  return result;
}

async function generatePlan({ scroll = true } = {}) {
  const plan = await api(`/generate-plan?source=${state.source}`, { method: "POST" });
  renderBriefing(plan);
  if (scroll) document.getElementById("command-briefing").scrollIntoView({ behavior: "smooth", block: "start" });
  toast("Command briefing generated", "success");
  return plan;
}

async function runFullJudgeDemo(button) {
  setBusy(button, true);
  setActionButtons(true);
  try {
    toast("Judge demo started: generating scenario", "info");
    setSource("demo", { render: false });
    await api("/simulate-crisis", { method: "POST" });
    toast("Scenario generated. Optimizing response allocation", "info");
    await api("/optimize-response?mode=quantum_inspired&source=demo", { method: "POST" });
    toast("Resources assigned. Generating command briefing", "info");
    const plan = await api("/generate-plan?source=demo", { method: "POST" });
    await loadAll();
    renderBriefing(plan);
    renderOutcome();
    document.getElementById("top").scrollIntoView({ behavior: "smooth", block: "start" });
    toast("Full judge demo complete", "success");
  } catch (error) {
    console.error(error);
    toast(`Judge demo failed: ${error.message}`, "error");
  } finally {
    setActionButtons(false);
    setBusy(button, false);
  }
}

function syncSourceButtons() {
  qa(".mode-pill").forEach((button) => {
    const active = button.dataset.source === state.source;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  setText("active-source-label", state.source === "voice" ? "Voice Calls" : "Demo Ops");
}

async function setSource(source, options = {}) {
  if (!["demo", "voice"].includes(source)) return;
  state.source = source;
  state.briefing = null;
  state.activeFilter = "all";
  qa(".filter-chip").forEach((item) => item.classList.toggle("active", item.dataset.filter === "all"));
  syncSourceButtons();
  if (options.render !== false) {
    renderBriefing(null);
    await loadAll();
    toast(`${source === "voice" ? "Voice call" : "Demo"} mode loaded`, "success");
  }
}

function initReveal() {
  const revealItems = qa(".reveal");
  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("visible"));
    return;
  }
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14, rootMargin: "0px 0px -50px 0px" });
  revealItems.forEach((item) => observer.observe(item));
}

function initCursorGlow() {
  const glow = document.querySelector(".cursor-glow");
  if (!glow || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  window.addEventListener("pointermove", (event) => {
    glow.style.left = `${event.clientX}px`;
    glow.style.top = `${event.clientY}px`;
  }, { passive: true });
}

function bindActions() {
  document.getElementById("btn-refresh").addEventListener("click", (event) => withButton(event.currentTarget, async () => {
    await loadAll();
    toast("Dashboard refreshed", "success");
  }));
  document.getElementById("btn-retry").addEventListener("click", () => loadAll());
  document.getElementById("btn-full-demo").addEventListener("click", (event) => runFullJudgeDemo(event.currentTarget));
  document.getElementById("btn-simulate").addEventListener("click", (event) => withButton(event.currentTarget, runSimulation));
  document.getElementById("btn-optimize").addEventListener("click", (event) => withButton(event.currentTarget, runOptimization));
  document.getElementById("btn-plan").addEventListener("click", (event) => withButton(event.currentTarget, () => generatePlan({ scroll: true })));
  document.getElementById("btn-plan-2").addEventListener("click", (event) => withButton(event.currentTarget, () => generatePlan({ scroll: false })));
  document.getElementById("btn-source-demo").addEventListener("click", (event) => withButton(event.currentTarget, () => setSource("demo")));
  document.getElementById("btn-source-voice").addEventListener("click", (event) => withButton(event.currentTarget, () => setSource("voice")));
  document.getElementById("btn-print-brief").addEventListener("click", () => window.print());
  document.getElementById("btn-copy-brief").addEventListener("click", async () => {
    if (!state.briefing) {
      toast("No briefing to copy yet", "info");
      return;
    }
    try {
      await navigator.clipboard.writeText(briefingMarkdown());
      toast("Briefing copied as Markdown", "success");
    } catch {
      toast("Copy failed. Browser clipboard access is unavailable.", "error");
    }
  });

  qa(".filter-chip").forEach((button) => {
    button.addEventListener("click", () => {
      qa(".filter-chip").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      state.activeFilter = button.dataset.filter || "all";
      renderIncidentTable();
    });
  });

  document.getElementById("intake-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type=submit]");
    const result = document.getElementById("intake-result");
    const formData = Object.fromEntries(new FormData(form).entries());
    formData.latitude = Number(formData.latitude);
    formData.longitude = Number(formData.longitude);

    result.className = "intake-result";
    result.innerHTML = "";
    setBusy(submit, true);
    try {
      const incident = await api("/incidents", {
        method: "POST",
        body: JSON.stringify({ ...formData, source: "web" }),
      });
      setSource("demo", { render: false });
      state.briefing = null;
      renderBriefing(null);
      await loadAll();
      const tier = incident.risk_tier || riskTier(Number(incident.priority_score || 0));
      result.className = "intake-result success";
      result.innerHTML = `
        <strong>Report classified. Rerun optimization to fold it into the deployment plan.</strong>
        <div class="result-grid">
          <div><strong>${formatNeed(incident.need_type)}</strong>need</div>
          <div><strong>${escapeHtml(incident.urgency || "unknown")}</strong>urgency</div>
          <div><strong>${Math.round(Number(incident.priority_score || 0))}</strong>score</div>
          <div><strong>${tier}</strong>risk</div>
        </div>
        <p style="margin-top:10px">${escapeHtml(incident.explanation || "")}</p>
      `;
      toast("Manual report submitted", "success");
      form.reset();
      form.querySelector("[name=latitude]").value = "43.6532";
      form.querySelector("[name=longitude]").value = "-79.3832";
    } catch (error) {
      result.className = "intake-result error";
      result.textContent = `Submission failed: ${error.message}`;
      toast("Manual report submission failed", "error");
    } finally {
      setBusy(submit, false);
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initReveal();
  initCursorGlow();
  syncSourceButtons();
  bindActions();
  renderBriefing(null);
  await loadAll();
  setInterval(checkHealth, 30000);
});

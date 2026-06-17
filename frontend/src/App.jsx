import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://localhost:8000";

function getRiskClass(level) {
  if (level === "high") return "pill danger";
  if (level === "medium") return "pill warning";
  return "pill success";
}

function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${Math.round(Number(value) * 100)}%`;
}

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [result, setResult] = useState(null);
  const [agentRuns, setAgentRuns] = useState([]);
  const [loading, setLoading] = useState(false);

  const [summary, setSummary] = useState(null);
  const [modelComparison, setModelComparison] = useState(null);
  const [featureImportance, setFeatureImportance] = useState([]);
  const [modelRegistry, setModelRegistry] = useState(null);
  const [driftStatus, setDriftStatus] = useState(null);
  const [patientSegments, setPatientSegments] = useState([]);
  const [patientExplanation, setPatientExplanation] = useState(null);
  const [riskForecast, setRiskForecast] = useState(null);

  useEffect(() => {
    fetchPatients();
    fetchAgentRuns();
    fetchDashboardSummary();
    fetchModelData();
    fetchPatientSegments();
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      fetchPatientMLInsights(selectedPatientId);
    }
  }, [selectedPatientId]);

  const fetchPatients = async () => {
    const res = await axios.get(`${API_BASE}/patients`);

    const validPatients = res.data.filter(
      (patient) => patient.patient_id && patient.medication
    );

    setPatients(validPatients);

    if (validPatients.length > 0) {
      setSelectedPatientId(validPatients[0].patient_id);
    }
  };

  const fetchAgentRuns = async () => {
    const res = await axios.get(`${API_BASE}/agent-runs`);
    setAgentRuns(res.data || []);
  };

  const fetchDashboardSummary = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/summary`);
      setSummary(res.data);
    } catch {
      setSummary(null);
    }
  };

  const fetchModelData = async () => {
    try {
      const [comparisonRes, importanceRes, registryRes, driftRes] =
        await Promise.all([
          axios.get(`${API_BASE}/model/compare`),
          axios.get(`${API_BASE}/model/feature-importance`),
          axios.get(`${API_BASE}/model/registry`),
          axios.get(`${API_BASE}/model/drift`),
        ]);

      setModelComparison(comparisonRes.data);
      setFeatureImportance(importanceRes.data || []);
      setModelRegistry(registryRes.data);
      setDriftStatus(driftRes.data);
    } catch (error) {
      console.error("Failed to load model data", error);
    }
  };

  const fetchPatientSegments = async () => {
    try {
      const res = await axios.get(`${API_BASE}/patients/segments`);
      setPatientSegments(res.data || []);
    } catch (error) {
      console.error("Failed to load patient segments", error);
    }
  };

  const fetchPatientMLInsights = async (patientId) => {
    try {
      const [explanationRes, forecastRes] = await Promise.all([
        axios.get(`${API_BASE}/patients/${patientId}/explanation`),
        axios.get(`${API_BASE}/patients/${patientId}/risk-forecast`),
      ]);

      setPatientExplanation(explanationRes.data);
      setRiskForecast(forecastRes.data);
    } catch (error) {
      console.error("Failed to load patient ML insights", error);
      setPatientExplanation(null);
      setRiskForecast(null);
    }
  };

  const runCheck = async () => {
    if (!selectedPatientId || selectedPatientId === "—") {
      alert("Please select a valid patient.");
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post(
        `${API_BASE}/run-adherence-check/${selectedPatientId}`
      );

      setResult(res.data);

      await Promise.all([
        fetchAgentRuns(),
        fetchDashboardSummary(),
        fetchPatientMLInsights(selectedPatientId),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const selectedPatient = patients.find(
    (patient) => patient.patient_id === selectedPatientId
  );

  const selectedSegment = patientSegments.find(
    (item) => item.patient_id === selectedPatientId
  );

  const safeRefill = result?.refill || {
    refill_status: "not_checked",
  };

  const safeEscalation = result?.escalation || {
    escalate: false,
    priority: "normal",
    reason: "Escalation was not required based on risk level",
  };

  const activeRisk = result?.risk || patientExplanation?.risk;
  const activeSegment = result?.segment || patientExplanation?.segment;
  const activeIntervention =
    result?.intervention || patientExplanation?.intervention;

  const bestModel = modelComparison?.best_model || "—";

  return (
    <div className="site">
      <header className="navbar">
        <div className="brand">
          <div className="brand-mark" aria-label="HealthAgent hospital icon">
            <svg
              viewBox="0 0 24 24"
              width="24"
              height="24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 21V5.8C4 4.8 4.8 4 5.8 4H18.2C19.2 4 20 4.8 20 5.8V21"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M2.5 21H21.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M9 21V16.5C9 15.7 9.7 15 10.5 15H13.5C14.3 15 15 15.7 15 16.5V21"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M12 7.5V12.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M9.5 10H14.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <strong>HealthAgent</strong>
            <span>Multi-Agent Adherence AI</span>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#workflow">Workflow</a>
          <a href="#agents">Agents</a>
          <a href="#ml">ML Intelligence</a>
          <a href="#activity">Runs</a>
        </nav>

        <div className="backend-status">
          <span></span>
          Connected
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="hero-badge">HealthAgent Demo</div>
            <h1>Spatial AI command center for medication adherence.</h1>
            <p>
              Run a synthetic patient through a multi-agent workflow that
              predicts adherence risk, segments patient behavior, recommends
              interventions, checks drift, and stores explainable workflow
              traces.
            </p>

            <div className="hero-actions">
              <a href="#workflow" className="primary-link">
                Run Workflow
              </a>
              <a href="#ml" className="secondary-link">
                View ML Layer
              </a>
            </div>
          </div>

          <div className="hero-card spatial-card">
            <div className="hero-card-top">
              <span>Live System Snapshot</span>
              <div className="dot-row">
                <i></i>
                <i></i>
                <i></i>
              </div>
            </div>

            <div className="metric-row">
              <div>
                <span>Total Patients</span>
                <strong>{summary?.total_patients ?? patients.length}</strong>
              </div>
              <div>
                <span>Agent Runs</span>
                <strong>{summary?.total_agent_runs ?? agentRuns.length}</strong>
              </div>
            </div>

            <div className="metric-row">
              <div>
                <span>High Risk</span>
                <strong>{summary?.high_risk_runs ?? 0}</strong>
              </div>
              <div>
                <span>Pending Reviews</span>
                <strong>{summary?.pending_reviews ?? 0}</strong>
              </div>
            </div>

            <div className="mini-workflow">
              <span>Risk</span>
              <b></b>
              <span>Segment</span>
              <b></b>
              <span>Intervention</span>
              <b></b>
              <span>Review</span>
            </div>
          </div>
        </section>

        <section id="workflow" className="workflow-section">
          <div className="section-heading">
            <span>Run the system</span>
            <h2>Patient adherence workflow</h2>
            <p>
              Choose a synthetic patient and run the full ML-backed multi-agent
              workflow.
            </p>
          </div>

          <div className="workflow-grid">
            <div className="workflow-card">
              <div className="card-heading">
                <span>01</span>
                <div>
                  <h3>Select patient</h3>
                  <p>Choose one synthetic record from PostgreSQL.</p>
                </div>
              </div>

              <label>Patient</label>
              <select
                value={selectedPatientId}
                onChange={(e) => {
                  setSelectedPatientId(e.target.value);
                  setResult(null);
                }}
              >
                <option value="">Select a patient</option>

                {patients.map((patient) => (
                  <option key={patient.patient_id} value={patient.patient_id}>
                    {patient.patient_id} — {patient.medication}
                  </option>
                ))}
              </select>

              {selectedPatient && (
                <div className="patient-card">
                  <div>
                    <span>Medication</span>
                    <strong>{selectedPatient.medication}</strong>
                  </div>
                  <div>
                    <span>Age</span>
                    <strong>{selectedPatient.age}</strong>
                  </div>
                  <div>
                    <span>Missed Doses</span>
                    <strong>{selectedPatient.missed_doses_last_30_days}</strong>
                  </div>
                  <div>
                    <span>Last Refill</span>
                    <strong>{selectedPatient.last_refill_days_ago} days</strong>
                  </div>
                </div>
              )}

              <button onClick={runCheck} disabled={loading || !selectedPatientId}>
                {loading ? "Running ML agents..." : "Run Agent Workflow"}
              </button>
            </div>

            <div id="activity" className="workflow-card activity-card">
              <div className="card-heading">
                <span>02</span>
                <div>
                  <h3>Recent runs</h3>
                  <p>Saved workflow traces from PostgreSQL.</p>
                </div>
              </div>

              {agentRuns.length === 0 ? (
                <div className="empty-mini">No agent runs yet.</div>
              ) : (
                <div className="activity-list">
                  {agentRuns.slice(0, 5).map((run) => (
                    <div className="activity-item" key={run.id}>
                      <div>
                        <strong>{run.patient_id}</strong>
                        <span>{run.review_status || run.refill_status}</span>
                      </div>
                      <span className={getRiskClass(run.risk_level)}>
                        {run.risk_level}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <section id="ml" className="ml-section">
          <div className="section-heading">
            <span>ML Intelligence</span>
            <h2>Model monitoring and explainability</h2>
            <p>
              The ML layer compares models, exposes feature importance, tracks
              registry metadata, and checks lightweight drift.
            </p>
          </div>

          <div className="ml-grid">
            <article className="ml-card model-card">
              <div className="agent-number">M1</div>
              <h3>Best Model</h3>
              <strong className="big-word">{bestModel}</strong>
              <p>Selected by F1-score during synthetic model training.</p>

              {modelComparison?.models && (
                <div className="model-list">
                  {modelComparison.models.map((model) => (
                    <div key={model.model} className="model-row">
                      <span>{model.model}</span>
                      <strong>{formatPercent(model.f1_score)}</strong>
                    </div>
                  ))}
                </div>
              )}
            </article>

            <article className="ml-card">
              <div className="agent-number">M2</div>
              <h3>Feature Importance</h3>
              <p>Top drivers used by the active model.</p>

              <div className="importance-list">
                {featureImportance.slice(0, 5).map((item) => (
                  <div key={item.feature} className="importance-item">
                    <div>
                      <span>{item.feature}</span>
                      <strong>{formatPercent(item.importance)}</strong>
                    </div>
                    <div className="importance-bar">
                      <i style={{ width: `${Number(item.importance) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="ml-card">
              <div className="agent-number">M3</div>
              <h3>Model Registry</h3>
              <p>Active model metadata and version tracking.</p>

              <div className="registry-box">
                <span>Active Version</span>
                <strong>{modelRegistry?.active_version || modelRegistry?.models?.[0]?.version || "—"}</strong>
              </div>

              <div className="registry-box">
                <span>Active File</span>
                <strong>{modelRegistry?.active_model || "risk_model.pkl"}</strong>
              </div>
            </article>

            <article className="ml-card">
              <div className="agent-number">M4</div>
              <h3>Drift Monitor</h3>
              <p>Compares live patient features against training baseline.</p>

              <span
                className={
                  driftStatus?.drift_detected
                    ? "pill danger"
                    : "pill success"
                }
              >
                {driftStatus?.drift_detected ? "Drift Detected" : "No Drift"}
              </span>

              <p className="subtle-text">
                {driftStatus?.recommendation || "No drift check available."}
              </p>
            </article>
          </div>
        </section>

        <section className="ml-section">
          <div className="section-heading">
            <span>Patient Intelligence</span>
            <h2>Selected patient ML profile</h2>
            <p>
              Patient-specific segmentation, forecast, intervention, and
              explainability for the selected record.
            </p>
          </div>

          <div className="patient-intel-grid">
            <article className="ml-card">
              <div className="agent-number">P1</div>
              <h3>Patient Segment</h3>
              <strong className="big-word">
                {activeSegment?.label || selectedSegment?.segment || "—"}
              </strong>
              <p>
                Method: {activeSegment?.method || "KMeans"}
              </p>
            </article>

            <article className="ml-card">
              <div className="agent-number">P2</div>
              <h3>Recommended Intervention</h3>
              <strong className="big-word intervention-word">
                {activeIntervention?.recommended_intervention || "—"}
              </strong>
              <p>
                Confidence:{" "}
                {activeIntervention?.confidence
                  ? formatPercent(activeIntervention.confidence)
                  : "—"}
              </p>
            </article>

            <article className="ml-card">
              <div className="agent-number">P3</div>
              <h3>14-Day Risk Forecast</h3>
              <div className="forecast-row">
                <div>
                  <span>Current</span>
                  <strong>{formatPercent(riskForecast?.current_risk)}</strong>
                </div>
                <div>
                  <span>Forecast</span>
                  <strong>{formatPercent(riskForecast?.forecast_14_day_risk)}</strong>
                </div>
              </div>
              <span className="pill warning">
                {riskForecast?.trend || "insufficient_history"}
              </span>
            </article>
          </div>
        </section>

        <section id="agents" className="agents-section">
          <div className="section-heading">
            <span>Agent outputs</span>
            <h2>What each agent decided</h2>
            <p>
              The system separates model prediction, segmentation, deterministic
              checks, intervention recommendation, and escalation logic.
            </p>
          </div>

          {!activeRisk ? (
            <div className="placeholder-panel">
              <h3>No result yet</h3>
              <p>
                Run the workflow above to see the multi-agent output rendered
                here.
              </p>
            </div>
          ) : (
            <div className="agent-layout">
              <article className="agent-feature risk-feature">
                <div className="agent-number">01</div>
                <h3>Risk Agent</h3>
                <p>
                  Predicts medication non-adherence risk using the active
                  scikit-learn model.
                </p>

                <div className="risk-score-block">
                  <div>
                    <span>Risk Score</span>
                    <strong>{activeRisk.risk_score}</strong>
                  </div>
                  <span className={getRiskClass(activeRisk.risk_level)}>
                    {activeRisk.risk_level}
                  </span>
                </div>

                <h4>Top Risk Factors</h4>
                <div className="reason-list">
                  {(activeRisk.top_factors || []).map((factor, index) => (
                    <div key={index}>
                      <strong>{factor.impact}</strong> — {factor.explanation}
                    </div>
                  ))}
                </div>

                {!activeRisk.top_factors && (
                  <div className="reason-list">
                    {(activeRisk.reasons || []).map((reason, index) => (
                      <div key={index}>✓ {reason}</div>
                    ))}
                  </div>
                )}
              </article>

              <div className="agent-stack">
                <article className="agent-small-card">
                  <div className="agent-number">02</div>
                  <h3>Segment Agent</h3>
                  <strong className="big-word">
                    {activeSegment?.label || "—"}
                  </strong>
                  <p>Groups patients using KMeans behavioral segmentation.</p>
                </article>

                <article className="agent-small-card">
                  <div className="agent-number">03</div>
                  <h3>Refill Agent</h3>
                  <strong className="big-word">
                    {safeRefill.refill_status}
                  </strong>

                  {"days_overdue" in safeRefill && (
                    <p>{safeRefill.days_overdue} days overdue</p>
                  )}

                  {"days_until_due" in safeRefill && (
                    <p>{safeRefill.days_until_due} days until due</p>
                  )}

                  {safeRefill.refill_status === "not_checked" && (
                    <p>Refill check was skipped for this risk level.</p>
                  )}
                </article>

                <article className="agent-small-card">
                  <div className="agent-number">04</div>
                  <h3>Intervention Agent</h3>
                  <strong className="big-word intervention-word">
                    {activeIntervention?.recommended_intervention || "—"}
                  </strong>
                  <p>
                    Confidence:{" "}
                    {activeIntervention?.confidence
                      ? formatPercent(activeIntervention.confidence)
                      : "—"}
                  </p>
                </article>

                <article className="agent-small-card">
                  <div className="agent-number">05</div>
                  <h3>Escalation Agent</h3>
                  <strong className="big-word">
                    {safeEscalation.escalate ? "Escalate" : "No Escalation"}
                  </strong>
                  <p>{safeEscalation.reason}</p>
                </article>
              </div>

              <article className="summary-feature">
                <div className="agent-number">06</div>
                <h3>Care Summary</h3>
                <p>{result?.summary || patientExplanation?.summary}</p>
              </article>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
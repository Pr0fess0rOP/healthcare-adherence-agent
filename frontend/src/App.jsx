import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://localhost:8000";

function getRiskClass(level) {
  if (level === "high") return "pill danger";
  if (level === "medium") return "pill warning";
  return "pill success";
}

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [result, setResult] = useState(null);
  const [agentRuns, setAgentRuns] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPatients();
    fetchAgentRuns();
  }, []);

  const fetchPatients = async () => {
    const res = await axios.get(`${API_BASE}/patients`);
    setPatients(res.data);

    if (res.data.length > 0) {
      setSelectedPatientId(res.data[0].patient_id);
    }
  };

  const fetchAgentRuns = async () => {
    const res = await axios.get(`${API_BASE}/agent-runs`);
    setAgentRuns(res.data);
  };

  const runCheck = async () => {
    if (!selectedPatientId) return;

    setLoading(true);
    try {
      const res = await axios.post(
        `${API_BASE}/run-adherence-check/${selectedPatientId}`
      );
      setResult(res.data);
      fetchAgentRuns();
    } finally {
      setLoading(false);
    }
  };

  const selectedPatient = patients.find(
    (patient) => patient.patient_id === selectedPatientId
  );

  const highRiskCount = agentRuns.filter((run) => run.risk_level === "high").length;
  const escalationCount = agentRuns.filter((run) => run.escalate === true).length;

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
            <div className="hero-badge">Synthetic Healthcare AI Demo</div>
            <h1>Medication adherence monitoring powered by multi-agent workflows.</h1>
            <p>
              Select a synthetic patient, run the adherence workflow, and review
              risk prediction, refill status, reminder generation, escalation logic,
              and care-team summary in one clean flow.
            </p>

            <div className="hero-actions">
              <a href="#workflow" className="primary-link">
                Run Workflow
              </a>
              <a href="#agents" className="secondary-link">
                View Agents
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
                <strong>{patients.length}</strong>
              </div>
              <div>
                <span>Agent Runs</span>
                <strong>{agentRuns.length}</strong>
              </div>
            </div>

            <div className="metric-row">
              <div>
                <span>High Risk</span>
                <strong>{highRiskCount}</strong>
              </div>
              <div>
                <span>Escalations</span>
                <strong>{escalationCount}</strong>
              </div>
            </div>

            <div className="mini-workflow">
              <span>Risk</span>
              <b></b>
              <span>Refill</span>
              <b></b>
              <span>Reminder</span>
              <b></b>
              <span>Escalate</span>
            </div>
          </div>
        </section>

        <section id="workflow" className="workflow-section">
          <div className="section-heading">
            <span>Run the system</span>
            <h2>Patient adherence workflow</h2>
            <p>
              This demo keeps the workflow simple: choose a synthetic patient,
              run the agents, and inspect the output.
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
                {loading ? "Running multi-agent workflow..." : "Run Agent Workflow"}
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
                        <span>{run.refill_status}</span>
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

        <section id="agents" className="agents-section">
          <div className="section-heading">
            <span>Agent outputs</span>
            <h2>What each agent decided</h2>
            <p>
              The system separates model prediction, deterministic checks,
              reminder generation, and escalation logic.
            </p>
          </div>

          {!result ? (
            <div className="placeholder-panel">
              <h3>No result yet</h3>
              <p>
                Run the workflow above to see the multi-agent output rendered here.
              </p>
            </div>
          ) : (
            <div className="agent-layout">
              <article className="agent-feature risk-feature">
                <div className="agent-number">01</div>
                <h3>Risk Agent</h3>
                <p>
                  Predicts medication non-adherence risk using a scikit-learn
                  Logistic Regression model.
                </p>

                <div className="risk-score-block">
                  <div>
                    <span>Risk Score</span>
                    <strong>{result.risk.risk_score}</strong>
                  </div>
                  <span className={getRiskClass(result.risk.risk_level)}>
                    {result.risk.risk_level}
                  </span>
                </div>

                <div className="reason-list">
                  {result.risk.reasons.map((reason, index) => (
                    <div key={index}>✓ {reason}</div>
                  ))}
                </div>
              </article>

              <div className="agent-stack">
                <article className="agent-small-card">
                  <div className="agent-number">02</div>
                  <h3>Refill Agent</h3>
                  <strong className="big-word">{result.refill.refill_status}</strong>
                  {"days_overdue" in result.refill && (
                    <p>{result.refill.days_overdue} days overdue</p>
                  )}
                  {"days_until_due" in result.refill && (
                    <p>{result.refill.days_until_due} days until due</p>
                  )}
                </article>

                <article className="agent-small-card">
                  <div className="agent-number">03</div>
                  <h3>Reminder Agent</h3>
                  <span className="channel">{result.reminder.channel}</span>
                  <p>{result.reminder.message}</p>
                </article>

                <article className="agent-small-card">
                  <div className="agent-number">04</div>
                  <h3>Escalation Agent</h3>
                  <strong className="big-word">
                    {result.escalation.escalate ? "Escalate" : "No Escalation"}
                  </strong>
                  <p>{result.escalation.reason}</p>
                </article>
              </div>

              <article className="summary-feature">
                <div className="agent-number">05</div>
                <h3>Care Summary</h3>
                <p>{result.summary}</p>
              </article>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
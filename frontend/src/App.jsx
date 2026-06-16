import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/patients`).then((res) => {
      setPatients(res.data);
      if (res.data.length > 0) {
        setSelectedPatientId(res.data[0].patient_id);
      }
    });
  }, []);

  const runCheck = async () => {
    const res = await axios.post(
      `${API_BASE}/run-adherence-check/${selectedPatientId}`
    );
    setResult(res.data);
  };

  return (
    <div className="app">
      <h1>Healthcare Adherence Multi-Agent Dashboard</h1>

      <div className="card">
        <h2>Run Adherence Check</h2>

        <div className="controls">
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
          >
            {patients.map((patient) => (
              <option key={patient.patient_id} value={patient.patient_id}>
                {patient.patient_id} - {patient.medication}
              </option>
            ))}
          </select>

          <button onClick={runCheck}>Run Agent Workflow</button>
        </div>
      </div>

      {result && (
        <div className="grid">
          <div className="card">
            <h2>Risk Agent</h2>
            <p>Risk Score: {result.risk.risk_score}</p>
            <p>Risk Level: {result.risk.risk_level}</p>
            <ul>
              {result.risk.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h2>Refill Agent</h2>
            <p>Status: {result.refill.refill_status}</p>
          </div>

          <div className="card">
            <h2>Reminder Agent</h2>
            <p>Channel: {result.reminder.channel}</p>
            <p>{result.reminder.message}</p>
          </div>

          <div className="card">
            <h2>Escalation Agent</h2>
            <p>Escalate: {String(result.escalation.escalate)}</p>
            <p>Priority: {result.escalation.priority}</p>
            <p>{result.escalation.reason}</p>
          </div>

          <div className="card full">
            <h2>Care Summary</h2>
            <p>{result.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
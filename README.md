# HealthAgent — Multi-Agent Medication Adherence AI

HealthAgent is a full-stack healthcare AI demo that simulates medication adherence monitoring using **synthetic patient data**. The system combines a FastAPI backend, PostgreSQL database, LangGraph multi-agent orchestration, scikit-learn machine learning models, audit logging, notification simulation, human-in-the-loop escalation review, and a React spatial UI frontend.

This project is for educational and portfolio purposes only. It does **not** use real patient data, PHI, EHR records, claims data, or pharmacy data.

---

## What HealthAgent Does

HealthAgent allows a user to select a synthetic patient and run a medication adherence workflow. The system then:

1. Predicts medication non-adherence risk using a trained scikit-learn model.
2. Explains the top risk factors for the patient.
3. Segments the patient using KMeans clustering.
4. Checks refill status when appropriate.
5. Generates a patient reminder message.
6. Recommends an intervention.
7. Escalates high-risk cases for human review.
8. Stores the full multi-agent trace in PostgreSQL.
9. Queues a simulated notification.
10. Writes audit logs for traceability.
11. Exposes model metrics, feature importance, model registry data, and drift monitoring.
12. Displays everything through a spatial UI React dashboard.

---

## Safety Note

This is a synthetic healthcare AI demo.

The system does not provide medical advice, diagnosis, or treatment recommendations. It only demonstrates how a multi-agent AI workflow could support adherence monitoring, explainability, escalation review, and operational traceability using synthetic data.

---

## Tech Stack

### Backend

- FastAPI
- PostgreSQL
- SQLAlchemy
- LangGraph
- scikit-learn
- pandas
- numpy
- joblib
- Uvicorn

### Machine Learning

- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier
- KMeans clustering
- Feature importance extraction
- Synthetic dataset generation
- Model comparison
- Model registry
- Drift monitoring
- Risk forecasting

### Frontend

- React
- Vite
- Axios
- CSS spatial UI
- Browser tab favicon
- HealthAgent hospital icon branding

### Infrastructure

- Docker Compose for PostgreSQL

---

## System Architecture

```text
React Spatial UI
      |
      v
FastAPI Backend
      |
      v
PostgreSQL
      |
      v
LangGraph Multi-Agent Workflow
      |
      v
scikit-learn ML Layer
```

---

## Multi-Agent Workflow

The workflow is orchestrated using LangGraph.

```text
Patient Data
   |
   v
Risk Agent
   |
   v
Segment Agent
   |
   v
Conditional Routing
   |
   |-- Low Risk ----------> Reminder Agent
   |
   |-- Medium/High Risk --> Refill Agent --> Reminder Agent
   |
   v
Intervention Agent
   |
   v
Conditional Routing
   |
   |-- High Risk ---------> Escalation Agent --> Summary Agent
   |
   |-- Low/Medium Risk ---> Summary Agent
```

---

## Agents

### 1. Risk Agent

Uses the active scikit-learn model to predict medication non-adherence risk.

Inputs:

- Age
- Last refill days ago
- Medication supply days
- Missed doses in the last 30 days
- Prior non-adherence history

Example output:

```json
{
  "risk_score": 0.91,
  "risk_level": "high",
  "model_type": "RandomForestClassifier",
  "top_factors": [
    {
      "factor": "missed_doses_last_30_days",
      "value": 6,
      "impact": "high",
      "explanation": "Patient has a high number of missed doses in the last 30 days."
    }
  ]
}
```

### 2. Segment Agent

Uses KMeans clustering to assign the patient to an adherence behavior segment.

Example output:

```json
{
  "cluster_id": 3,
  "label": "High-touch adherence support",
  "method": "KMeans"
}
```

### 3. Refill Agent

Checks refill status.

Possible values:

```text
not_due
due_soon
overdue
not_checked
```

Low-risk patients may skip the refill check through conditional routing.

### 4. Reminder Agent

Generates a simulated reminder message based on patient risk and refill status.

Example:

```text
Hi, this is a reminder that your Atorvastatin refill may be overdue. Please check with your pharmacy or care team.
```

### 5. Intervention Agent

Recommends the next-best intervention based on risk level, refill status, patient segment, and missed-dose behavior.

Example output:

```json
{
  "recommended_intervention": "Care coordinator follow-up with pharmacy refill support",
  "confidence": 0.9,
  "based_on": {
    "risk_level": "high",
    "refill_status": "overdue",
    "segment": "High-touch adherence support"
  }
}
```

### 6. Escalation Agent

Flags high-risk cases for human review.

Example output:

```json
{
  "escalate": true,
  "priority": "high",
  "reason": "Patient should be reviewed by care team"
}
```

### 7. Summary Agent

Creates the final care-team summary.

Example:

```text
Patient P1002 is at high risk for medication non-adherence. Segment: High-touch adherence support. Refill status is overdue. Recommended intervention: Care coordinator follow-up with pharmacy refill support. Escalation required: True.
```

---

## Machine Learning Features

### Model Training Pipeline

The training script generates synthetic adherence data and trains multiple models:

- LogisticRegression
- RandomForestClassifier
- GradientBoostingClassifier

The best model is selected by F1-score and saved as:

```text
backend/app/ml/risk_model.pkl
```

The pipeline also saves:

```text
model_metrics.json
model_comparison.json
feature_importance.json
model_registry.json
drift_baseline.json
cluster_model.pkl
cluster_scaler.pkl
```

### Model Comparison

```http
GET /model/compare
```

Example response:

```json
{
  "best_model": "RandomForestClassifier",
  "selected_by": "f1_score",
  "models": [
    {
      "model": "RandomForestClassifier",
      "accuracy": 0.91,
      "precision": 0.90,
      "recall": 0.93,
      "f1_score": 0.91
    }
  ]
}
```

### Feature Importance

```http
GET /model/feature-importance
```

Example response:

```json
[
  {
    "feature": "missed_doses_last_30_days",
    "importance": 0.36
  },
  {
    "feature": "last_refill_days_ago",
    "importance": 0.31
  }
]
```

### Model Registry

```http
GET /model/registry
```

Example response:

```json
{
  "active_model": "risk_model.pkl",
  "active_version": "v20260616T120000",
  "models": [
    {
      "version": "v20260616T120000",
      "model_file": "risk_model.pkl",
      "model_type": "RandomForestClassifier",
      "f1_score": 0.91
    }
  ]
}
```

### Drift Monitoring

```http
GET /model/drift
```

The drift monitor compares live synthetic patient feature distributions against the training baseline.

Example response:

```json
{
  "drift_detected": false,
  "drifted_features": [],
  "recommendation": "No major drift detected."
}
```

### Patient Risk Forecast

```http
GET /patients/{patient_id}/risk-forecast
```

Example response:

```json
{
  "patient_id": "P1002",
  "current_risk": 0.81,
  "forecast_14_day_risk": 0.86,
  "trend": "increasing",
  "method": "simple trend + refill/missed-dose heuristic"
}
```

---

## Human-in-the-Loop Review

High-risk cases are marked as pending review instead of being automatically approved.

Review statuses:

```text
not_required
pending
approved
rejected
```

Endpoint:

```http
PATCH /agent-runs/{run_id}/review
```

Request body:

```json
{
  "review_status": "approved",
  "review_notes": "High-risk patient with overdue refill. Care team follow-up approved."
}
```

---

## Notification Simulation

HealthAgent does not send real SMS or email. It queues simulated notifications.

Notification statuses:

```text
queued
sent
failed
```

Endpoints:

```http
GET /notifications
POST /notifications/{notification_id}/mark-sent
POST /notifications/{notification_id}/mark-failed
```

---

## Audit Logging

The backend writes audit logs for traceability.

Examples:

```text
PATIENTS_LISTED
ADHERENCE_CHECK_RUN
NOTIFICATION_QUEUED
NOTIFICATION_SENT
NOTIFICATION_FAILED
ESCALATION_REVIEWED
```

Endpoint:

```http
GET /audit-logs
```

---

## Frontend Features

The React frontend uses a spatial UI design and displays:

- HealthAgent branding with a hospital icon
- Browser tab favicon
- Live system snapshot
- Patient selector
- Recent agent runs
- Best model and model comparison
- Feature importance bars
- Model registry
- Drift monitor
- Patient segment
- Recommended intervention
- 14-day risk forecast
- Risk agent output with top factors
- Segment agent output
- Refill agent output
- Intervention agent output
- Escalation agent output
- Care summary

---

## Folder Structure

```text
healthcare-adherence-agent/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   │
│   │   ├── agents/
│   │   │   ├── risk_agent.py
│   │   │   ├── segment_agent.py
│   │   │   ├── refill_agent.py
│   │   │   ├── reminder_agent.py
│   │   │   ├── intervention_agent.py
│   │   │   ├── escalation_agent.py
│   │   │   └── summary_agent.py
│   │   │
│   │   ├── workflow/
│   │   │   └── adherence_graph.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── audit_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   └── ml/
│   │       ├── train_model.py
│   │       ├── ml_utils.py
│   │       ├── risk_model.pkl
│   │       ├── cluster_model.pkl
│   │       ├── cluster_scaler.pkl
│   │       ├── model_metrics.json
│   │       ├── model_comparison.json
│   │       ├── feature_importance.json
│   │       ├── model_registry.json
│   │       └── drift_baseline.json
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
```

---

## Database Tables

### patients

Stores synthetic patient records.

```text
patient_id
age
medication
last_refill_days_ago
supply_days
missed_doses_last_30_days
prior_non_adherence
preferred_contact
```

### agent_runs

Stores full multi-agent workflow outputs.

```text
patient_id
risk_score
risk_level
refill_status
escalate
priority
review_status
review_notes
reviewed_at
full_trace
created_at
```

### notifications

Stores simulated notification events.

```text
patient_id
agent_run_id
channel
message
status
created_at
updated_at
```

### audit_logs

Stores traceability events.

```text
action
entity_type
entity_id
details
created_at
```

---

## API Routes

### Health Check

```http
GET /
```

### Patients

```http
GET /patients
GET /patients/segments
GET /patients/{patient_id}/risk-history
GET /patients/{patient_id}/explanation
GET /patients/{patient_id}/intervention
GET /patients/{patient_id}/risk-forecast
```

Important: define `/patients/segments` before dynamic routes like `/patients/{patient_id}/risk-history`.

### Agent Workflow

```http
POST /run-adherence-check/{patient_id}
GET /agent-runs
PATCH /agent-runs/{run_id}/review
```

### Dashboard

```http
GET /dashboard/summary
```

### Notifications

```http
GET /notifications
POST /notifications/{notification_id}/mark-sent
POST /notifications/{notification_id}/mark-failed
```

### Machine Learning

```http
GET /model/metrics
GET /model/compare
GET /model/feature-importance
GET /model/registry
GET /model/drift
```

### Audit Logs

```http
GET /audit-logs
```

---

## How to Run the Project

### 1. Start PostgreSQL

Make sure Docker Desktop is running.

From the project root:

```bash
docker compose up -d
```

This starts PostgreSQL with:

```text
Database: adherence_db
User: adherence_user
Password: adherence_pass
Port: 5432
```

### 2. Start Backend

Go to the backend folder:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows PowerShell:

```powershell
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Seed synthetic patients:

```bash
python -m app.seed
```

Train ML models:

```bash
python -m app.ml.train_model
```

Run FastAPI:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

### 3. Start Frontend

Open a new terminal.

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

If Vite uses another port such as `5174`, add it to the FastAPI CORS config.

---

## Recommended Test Flow

### 1. Check backend

```text
http://localhost:8000
```

Expected:

```json
{
  "message": "HealthAgent API is running"
}
```

### 2. Check patients

```text
http://localhost:8000/patients
```

Expected:

```json
[
  {
    "patient_id": "P1001",
    "medication": "Metformin"
  },
  {
    "patient_id": "P1002",
    "medication": "Atorvastatin"
  }
]
```

### 3. Run workflow

PowerShell:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run-adherence-check/P1002"
```

Expected response includes:

```text
risk
segment
refill
reminder
intervention
escalation
summary
```

### 4. Review escalation

Get agent run IDs:

```text
http://localhost:8000/agent-runs
```

Review a pending run:

```http
PATCH /agent-runs/1/review
```

Request:

```json
{
  "review_status": "approved",
  "review_notes": "High-risk patient with overdue refill. Follow-up approved."
}
```

### 5. Open React UI

```text
http://localhost:5173
```

Select a patient and click:

```text
Run Agent Workflow
```

---

## Troubleshooting

### Docker command not found

Install Docker Desktop and restart PowerShell.

```bash
docker --version
docker compose version
```

### Docker daemon not running

Open Docker Desktop and wait until Docker Engine is running.

```bash
docker compose up -d
```

### PowerShell curl issue

Use:

```powershell
curl.exe -X POST http://localhost:8000/run-adherence-check/P1002
```

or:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run-adherence-check/P1002"
```

### CORS error

If frontend runs on `5174`, add it to FastAPI CORS:

```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
```

### Dropdown shows only dashes

Check:

```text
http://localhost:8000/patients
```

If it returns:

```json
[{},{},{}]
```

make sure the `/patients` endpoint returns dictionaries or uses a Pydantic response model.

### React crashes on low-risk patients

Low-risk patients may skip `refill_agent`. Use safe frontend fallbacks:

```javascript
const safeRefill = result?.refill || {
  refill_status: "not_checked",
};
```

Also make sure `summary_agent.py` returns fallback `refill` and `escalation` objects.

### `/patients/segments` fails

Define `/patients/segments` before dynamic patient routes in `main.py`.

---

## Demo Patient

Use:

```text
P1002 — Atorvastatin
```

This patient usually demonstrates the full workflow:

```text
Older age
Overdue refill
Multiple missed doses
Prior non-adherence history
High-risk classification
Escalation review
Intervention recommendation
Queued notification
Audit logs
```

---

## Future Improvements

1. Add authentication and role-based access control.
2. Add charts for risk trends and model metrics.
3. Add a full escalation review page in React.
4. Add notification inbox and simulated delivery controls.
5. Add Alembic migrations instead of resetting the database.
6. Add SHAP for richer model explainability.
7. Add synthetic longitudinal patient history.
8. Deploy backend on AWS ECS, Lambda, RDS, or App Runner.
9. Deploy frontend on Vercel, Netlify, or AWS Amplify.
10. Add CI/CD using GitHub Actions.
11. Add tests for agents, APIs, and ML utility functions.

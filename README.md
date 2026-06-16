# Healthcare Adherence Multi-Agent System

A full-stack multi-agent healthcare adherence demo that identifies medication non-adherence risk using synthetic patient data. The system uses a FastAPI backend, PostgreSQL database, LangGraph workflow orchestration, a scikit-learn risk prediction model, and a React dashboard.

This project is built as a safe healthcare AI demo. It does not use real patient data or PHI. All patient records are synthetic.

---

## What This Project Does

This application simulates how a healthcare platform could monitor medication adherence risk.

The system allows a user to:

1. View synthetic patients from a database.
2. Select a patient in the React dashboard.
3. Run a multi-agent adherence check.
4. Predict the patient's non-adherence risk using a scikit-learn model.
5. Check whether the medication refill is overdue or due soon.
6. Generate a patient-friendly reminder message.
7. Decide whether the patient should be escalated for care-team review.
8. Generate a short care-team summary.
9. Save the full agent trace into PostgreSQL.

The main purpose is to demonstrate production-style AI architecture with clear separation between deterministic logic, machine learning, and multi-agent workflow orchestration.

---

## Tech Stack

### Backend

- FastAPI
- PostgreSQL
- SQLAlchemy
- LangGraph
- scikit-learn
- pandas
- joblib
- Uvicorn

### Frontend

- React
- Vite
- Axios
- CSS

### Infrastructure

- Docker Compose for PostgreSQL

---

## Multi-Agent Workflow

The system uses a LangGraph workflow with multiple specialized agents.

```text
Patient Data
   |
   v
Risk Agent
   |
   v
Refill Agent
   |
   v
Reminder Agent
   |
   v
Escalation Agent
   |
   v
Summary Agent
```

### 1. Risk Agent

Uses a scikit-learn Logistic Regression model to estimate the patient's non-adherence risk.

Inputs include:

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
  "model_type": "LogisticRegression"
}
```

---

### 2. Refill Agent

Checks whether the medication refill is:

- `not_due`
- `due_soon`
- `overdue`

Example output:

```json
{
  "refill_status": "overdue",
  "days_overdue": 11
}
```

---

### 3. Reminder Agent

Generates a simple reminder message based on the patient's medication and refill status.

Example:

```text
Hi, this is a reminder that your Atorvastatin refill may be overdue. Please check with your pharmacy or care team.
```

---

### 4. Escalation Agent

Decides whether the patient should be reviewed by the care team.

Escalation is triggered when:

- Risk level is high
- Refill is overdue

Example output:

```json
{
  "escalate": true,
  "priority": "high",
  "reason": "Patient should be reviewed by care team"
}
```

---

### 5. Summary Agent

Creates a short care-team summary.

Example:

```text
Patient P1002 is at high risk for medication non-adherence. Refill status is overdue. Escalation required: true.
```

---

## Folder Structure

```text
healthcare-adherence-agent/
|
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   ├── __init__.py
│   │   │
│   │   ├── agents/
│   │   │   ├── risk_agent.py
│   │   │   ├── refill_agent.py
│   │   │   ├── reminder_agent.py
│   │   │   ├── escalation_agent.py
│   │   │   └── summary_agent.py
│   │   │
│   │   ├── workflow/
│   │   │   └── adherence_graph.py
│   │   │
│   │   └── ml/
│   │       ├── train_model.py
│   │       └── risk_model.pkl
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
```

---

## Backend Setup

### 1. Open the project

```bash
cd healthcare-adherence-agent
```

---

### 2. Start PostgreSQL with Docker

Make sure Docker Desktop is running.

From the project root:

```bash
docker compose up -d
```

This starts a PostgreSQL container with:

```text
Database: adherence_db
User: adherence_user
Password: adherence_pass
Port: 5432
```

---

### 3. Create and activate Python virtual environment

Go to the backend folder:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv venv
```

Activate it.

For Windows PowerShell:

```powershell
venv\Scripts\activate
```

For Mac/Linux:

```bash
source venv/bin/activate
```

---

### 4. Install backend dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Seed synthetic patient data

From the `backend` folder:

```bash
python -m app.seed
```

Expected output:

```text
Seeded synthetic patients.
```

---

### 6. Train the scikit-learn risk model

From the `backend` folder:

```bash
python -m app.ml.train_model
```

Expected output:

```text
Model evaluation:
...
Saved model to: .../backend/app/ml/risk_model.pkl
```

This creates the model file used by the Risk Agent.

---

### 7. Run the FastAPI backend

From the `backend` folder:

```bash
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://localhost:8000
```

Swagger API docs are available at:

```text
http://localhost:8000/docs
```

---

## Frontend Setup

Open a new terminal and go to the frontend folder:

```bash
cd healthcare-adherence-agent/frontend
```

Install dependencies:

```bash
npm install
```

Start the React development server:

```bash
npm run dev
```

Frontend will usually run at:

```text
http://localhost:5173
```

If port `5173` is busy, Vite may run on:

```text
http://localhost:5174
```

Make sure the backend CORS settings include the frontend port.

---

## API Routes

### Root Health Check

```http
GET /
```

Example response:

```json
{
  "message": "Healthcare Adherence API is running"
}
```

---

### Get All Patients

```http
GET /patients
```

Returns all synthetic patients from PostgreSQL.

Example response:

```json
[
  {
    "patient_id": "P1001",
    "age": 45,
    "medication": "Metformin",
    "last_refill_days_ago": 22,
    "supply_days": 30,
    "missed_doses_last_30_days": 1,
    "prior_non_adherence": false,
    "preferred_contact": "sms"
  }
]
```

---

### Run Multi-Agent Adherence Check

```http
POST /run-adherence-check/{patient_id}
```

Example:

```http
POST /run-adherence-check/P1002
```

Example response:

```json
{
  "patient": {
    "patient_id": "P1002",
    "age": 67,
    "medication": "Atorvastatin",
    "last_refill_days_ago": 41,
    "supply_days": 30,
    "missed_doses_last_30_days": 6,
    "prior_non_adherence": true,
    "preferred_contact": "email"
  },
  "risk": {
    "risk_score": 0.91,
    "risk_level": "high",
    "reasons": [
      "Refill is overdue",
      "High number of missed doses in last 30 days",
      "Patient has prior non-adherence history",
      "Patient is 65 or older",
      "ML model estimated non-adherence probability at 0.91"
    ],
    "model_type": "LogisticRegression"
  },
  "refill": {
    "refill_status": "overdue",
    "days_overdue": 11
  },
  "reminder": {
    "channel": "email",
    "message": "Hi, this is a reminder that your Atorvastatin refill may be overdue. Please check with your pharmacy or care team.",
    "risk_level": "high"
  },
  "escalation": {
    "escalate": true,
    "priority": "high",
    "reason": "Patient should be reviewed by care team"
  },
  "summary": "Patient P1002 is at high risk for medication non-adherence. Refill status is overdue. Escalation required: True."
}
```

This endpoint also saves the full agent trace into PostgreSQL.

---

### Get Saved Agent Runs

```http
GET /agent-runs
```

Returns all previous agent workflow runs stored in the database.

Example response:

```json
[
  {
    "patient_id": "P1002",
    "risk_score": 0.91,
    "risk_level": "high",
    "refill_status": "overdue",
    "escalate": true,
    "priority": "high",
    "full_trace": {
      "patient": {},
      "risk": {},
      "refill": {},
      "reminder": {},
      "escalation": {},
      "summary": "..."
    }
  }
]
```

---

## How to Test the Project

### 1. Confirm backend is running

Open:

```text
http://localhost:8000
```

You should see:

```json
{
  "message": "Healthcare Adherence API is running"
}
```

---

### 2. Confirm patient data exists

Open:

```text
http://localhost:8000/patients
```

You should see patients like:

```text
P1001
P1002
P1003
```

If this returns an empty list, run:

```bash
python -m app.seed
```

---

### 3. Run an agent workflow manually

PowerShell:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run-adherence-check/P1002"
```

Or use Swagger:

```text
http://localhost:8000/docs
```

---

### 4. Test from React dashboard

Open the frontend URL:

```text
http://localhost:5173
```

Then:

1. Select a patient.
2. Click `Run Agent Workflow`.
3. Check the result cards:
   - Risk Agent
   - Refill Agent
   - Reminder Agent
   - Escalation Agent
   - Care Summary

---

## Example Demo Flow

Use patient `P1002`.

This patient has:

```text
Age: 67
Medication: Atorvastatin
Last refill: 41 days ago
Supply days: 30
Missed doses: 6
Prior non-adherence: true
Preferred contact: email
```

Expected result:

```text
Risk Level: high
Refill Status: overdue
Escalation: true
Priority: high
```

This is the best demo patient because it clearly triggers the full workflow.

---

## Database Tables

### patients

Stores synthetic patient records.

Important fields:

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

---

### agent_runs

Stores each multi-agent workflow execution.

Important fields:

```text
patient_id
risk_score
risk_level
refill_status
escalate
priority
full_trace
created_at
```

The `full_trace` field stores the complete output from every agent.

---

## Important Safety Note

This project is for educational and portfolio purposes only.

It uses synthetic healthcare data and does not process real patient health information.

The system does not provide medical advice, diagnosis, or treatment recommendations. It only demonstrates how a multi-agent AI workflow could assist with adherence monitoring and care-team review workflows.

---

## Current Limitations

- Uses synthetic data only.
- Risk model is trained on a small handcrafted dataset.
- Reminder messages are simulated and not actually sent.
- No authentication or role-based access control yet.
- No real EHR, pharmacy, or claims system integration.
- No human approval workflow yet.

---

## Future Improvements

Potential next steps:

1. Add a larger synthetic dataset.
2. Add model evaluation metrics dashboard.
3. Add human-in-the-loop approval before escalation.
4. Add Twilio SMS or email notification simulation.
5. Add authentication and role-based access control.
6. Add care coordinator dashboard for reviewing escalations.
7. Add charts for risk trends and missed dose history.
8. Deploy backend on AWS using Lambda or ECS.
9. Deploy frontend on Vercel or AWS Amplify.
10. Add audit logs for every agent decision.

---

## Resume Summary

This project demonstrates:

- Multi-agent AI system design
- FastAPI backend development
- PostgreSQL data modeling
- LangGraph workflow orchestration
- scikit-learn risk prediction
- React dashboard development
- Explainable agent traces
- Healthcare AI safety awareness using synthetic data only

Example resume bullet:

```text
Built a full-stack multi-agent healthcare adherence system using FastAPI, PostgreSQL, LangGraph, scikit-learn, and React to predict medication non-adherence risk, monitor refill status, generate patient reminders, and escalate high-risk cases with explainable agent traces.
```

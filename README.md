# Mini EDR — Endpoint Detection & Response Starter

A small, self-hostable Endpoint Detection and Response (EDR) platform you can
run on machines **you own or are authorized to monitor**. It's meant as a
learning project / portfolio piece that mirrors the architectural ideas
behind tools like Wazuh, OSQuery + Fleet, or CrowdStrike — at a scale you can
actually read in an afternoon.

## Architecture

```
 ┌────────────────────┐        HTTPS / JSON         ┌──────────────────────┐
 │   React Dashboard   │ <--------------------------> │   FastAPI Backend     │
 │  (frontend/)        │                              │  (backend/)           │
 └────────────────────┘                              └──────────┬───────────┘
                                                                  │
                                                          SQLAlchemy ORM
                                                                  │
                                                          ┌───────▼────────┐
                                                          │ SQLite / Postgres│
                                                          └───────┬────────┘
                                                                  │
                                                          REST API (polling)
                                                                  │
                  ┌────────────────────────┬─────────────────────┴───┐
                  │                         │                          │
          ┌───────▼──────┐         ┌────────▼──────┐          ┌────────▼──────┐
          │ Agent (host A)│         │ Agent (host B) │          │ Agent (host C) │
          │ agent/agent.py│         │ agent/agent.py │          │ agent/agent.py │
          └───────────────┘         └────────────────┘          └────────────────┘
```

Each **agent** is a small Python script (using `psutil`) that runs on a
monitored endpoint. It periodically:

1. Registers itself with the backend (hostname, OS, IP).
2. Sends a heartbeat with CPU/RAM/uptime so the dashboard can show
   online/offline status.
3. Uploads a snapshot of running processes.
4. Hashes a configurable list of important files/directories and raises an
   **alert** if any of them change unexpectedly (basic file integrity
   monitoring).

The **backend** is a FastAPI app backed by SQLAlchemy (SQLite by default,
swap to Postgres by changing `DATABASE_URL`). It exposes a REST API that both
the agents and the dashboard talk to.

The **frontend** is a React + Vite single-page dashboard showing:

- A device list (hostname, OS, IP, status, last seen)
- A device detail view with live system stats and a process table
- An alerts panel for file-integrity and other events

## Project layout

```
mini-edr/
├── backend/            FastAPI server + SQLAlchemy models
│   ├── app/
│   │   ├── main.py         App entrypoint, CORS, router registration
│   │   ├── database.py     Engine / session setup
│   │   ├── models.py        Agent, ProcessSnapshot, Alert, FileRecord
│   │   ├── schemas.py       Pydantic request/response models
│   │   └── routers/
│   │       ├── agents.py    Registration, heartbeat, device list
│   │       ├── processes.py Process snapshot upload/retrieval
│   │       └── alerts.py    Alert creation/listing/resolution
│   └── requirements.txt
├── agent/              Endpoint agent
│   ├── agent.py
│   ├── config.yaml
│   └── requirements.txt
├── frontend/           React dashboard (Vite)
│   ├── src/
│   └── package.json
└── docker-compose.yml  Optional: backend + Postgres + frontend
```

## Quick start (SQLite, no Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be at `http://localhost:8000` and interactive docs at
`http://localhost:8000/docs`. A `mini_edr.db` SQLite file is created
automatically.

### 2. Agent

Run this **only on machines you own / are authorized to monitor**.

```bash
cd agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Edit config.yaml: set server_url and (optionally) files to integrity-check
python agent.py
```

On first run the agent registers itself and saves its assigned `agent_id`
into `agent_state.json` so subsequent runs update the same device record.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`). The
dashboard talks to the backend at `http://localhost:8000` by default — change
`VITE_API_URL` in `frontend/.env` if your backend runs elsewhere.

## Running with Docker Compose (backend + Postgres + frontend)

```bash
docker compose up --build
```

This brings up Postgres, the FastAPI backend (using `DATABASE_URL` pointing
at Postgres), and the frontend dev server. Run agents separately on the
machines you want to monitor, pointed at the backend's URL.

## API overview

| Method | Path                              | Purpose                              |
|--------|-----------------------------------|---------------------------------------|
| POST   | `/api/agents/register`            | Register a new agent, returns its ID |
| POST   | `/api/agents/{id}/heartbeat`      | Update system stats / last-seen      |
| GET    | `/api/agents`                     | List all known devices               |
| GET    | `/api/agents/{id}`                | Get one device's details             |
| POST   | `/api/agents/{id}/processes`      | Upload current process list          |
| GET    | `/api/agents/{id}/processes`      | Get latest process snapshot          |
| POST   | `/api/agents/{id}/alerts`         | Raise an alert (e.g. file changed)   |
| GET    | `/api/alerts`                     | List alerts (filter by agent/status) |
| PATCH  | `/api/alerts/{id}/resolve`        | Mark an alert as resolved            |

## Extending this project

This scaffold deliberately covers the "core loop" — register, heartbeat,
process snapshot, alerts — so you can build outward:

- **Authentication**: add API keys per agent and login for the dashboard
  (FastAPI's `OAuth2PasswordBearer` + JWT is a natural fit).
- **WebSockets**: replace polling with a WebSocket channel for real-time
  process/alert streaming.
- **Detection rules**: add a rules engine that inspects incoming process
  snapshots against a watchlist (e.g. flag `mimikatz.exe`, unsigned
  binaries in `%TEMP%`, etc.) and auto-generates alerts.
- **MITRE ATT&CK mapping**: tag alert types with ATT&CK technique IDs and
  show them on the dashboard.
- **Role-based access control**: add user accounts with `admin` / `viewer`
  roles.

## Legal / ethical note

Only deploy the agent on systems you own or have explicit written
authorization to monitor. Installing monitoring software on systems without
consent is illegal in most jurisdictions, regardless of the tool's intent.

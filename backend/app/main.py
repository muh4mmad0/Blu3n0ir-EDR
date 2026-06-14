"""Mini EDR backend entrypoint.

Run with:

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import Base, engine
from .routers import agents, alerts, processes

# Create tables on startup if they don't exist yet. For anything beyond a
# starter project, switch to a migration tool such as Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini EDR API",
    description=(
        "Backend for a small Endpoint Detection and Response platform. "
        "Provides agent registration, heartbeats, process snapshots, "
        "and alerting."
    ),
    version="0.1.0",
)

# Wide-open CORS for local development. Restrict this to your dashboard's
# origin before deploying anywhere outside your own machine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(processes.router)
app.include_router(alerts.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}

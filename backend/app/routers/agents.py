"""Endpoints for agent registration, heartbeats, and device listing."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/agents", tags=["agents"])

# An agent that hasn't sent a heartbeat within this window is considered offline.
OFFLINE_THRESHOLD_SECONDS = 90


def _refresh_status(agent: models.Agent) -> None:
    """Mark an agent online/offline based on how recently it checked in."""
    last_seen = agent.last_seen
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    age = (datetime.now(timezone.utc) - last_seen).total_seconds()
    agent.status = (
        models.AgentStatus.online
        if age <= OFFLINE_THRESHOLD_SECONDS
        else models.AgentStatus.offline
    )


@router.post("/register", response_model=schemas.AgentOut)
def register_agent(payload: schemas.AgentRegister, db: Session = Depends(get_db)):
    """Register a new endpoint and return its assigned agent ID.

    Agents should call this once and persist the returned `id` locally,
    then use it for all subsequent heartbeat/process/alert calls.
    """
    agent = models.Agent(
        hostname=payload.hostname,
        os=payload.os,
        os_version=payload.os_version,
        ip_address=payload.ip_address,
        status=models.AgentStatus.online,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/{agent_id}/heartbeat", response_model=schemas.AgentOut)
def heartbeat(
    agent_id: str, payload: schemas.AgentHeartbeat, db: Session = Depends(get_db)
):
    """Update an agent's live stats and mark it as recently seen."""
    agent = db.get(models.Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")

    agent.last_seen = datetime.now(timezone.utc)
    agent.status = models.AgentStatus.online

    if payload.cpu_percent is not None:
        agent.cpu_percent = payload.cpu_percent
    if payload.ram_percent is not None:
        agent.ram_percent = payload.ram_percent
    if payload.uptime_seconds is not None:
        agent.uptime_seconds = payload.uptime_seconds
    if payload.ip_address is not None:
        agent.ip_address = payload.ip_address

    db.commit()
    db.refresh(agent)
    return agent


@router.get("", response_model=list[schemas.AgentOut])
def list_agents(db: Session = Depends(get_db)):
    """List all known devices, with status recomputed from last-seen time."""
    agents = db.query(models.Agent).order_by(models.Agent.hostname).all()
    for agent in agents:
        _refresh_status(agent)
    db.commit()
    return agents


@router.get("/{agent_id}", response_model=schemas.AgentOut)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(models.Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    _refresh_status(agent)
    db.commit()
    return agent

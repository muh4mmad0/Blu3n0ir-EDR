"""Endpoints for raising, listing, and resolving alerts."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["alerts"])


@router.post("/agents/{agent_id}/alerts", response_model=schemas.AlertOut)
def create_alert(
    agent_id: str, payload: schemas.AlertIn, db: Session = Depends(get_db)
):
    """Raise an alert for an agent (e.g. a file-integrity change)."""
    agent = db.get(models.Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")

    alert = models.Alert(
        agent_id=agent_id,
        alert_type=payload.alert_type,
        severity=payload.severity,
        message=payload.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alerts", response_model=list[schemas.AlertOut])
def list_alerts(
    agent_id: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List alerts, optionally filtered by agent and/or resolved status."""
    query = db.query(models.Alert)
    if agent_id is not None:
        query = query.filter(models.Alert.agent_id == agent_id)
    if resolved is not None:
        query = query.filter(models.Alert.resolved == resolved)

    return query.order_by(models.Alert.created_at.desc()).all()


@router.patch("/alerts/{alert_id}/resolve", response_model=schemas.AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(models.Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Unknown alert_id")

    alert.resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert

"""Endpoints for uploading and retrieving process snapshots."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/agents", tags=["processes"])


@router.post("/{agent_id}/processes", response_model=list[schemas.ProcessOut])
def upload_processes(
    agent_id: str, payload: schemas.ProcessSnapshotIn, db: Session = Depends(get_db)
):
    """Replace an agent's stored process list with the latest snapshot.

    The dashboard only needs "what's running right now", so each upload
    deletes the previous snapshot rather than accumulating history. If you
    want historical process data, append instead and add a time filter to
    the GET endpoint.
    """
    agent = db.get(models.Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")

    db.query(models.ProcessSnapshot).filter(
        models.ProcessSnapshot.agent_id == agent_id
    ).delete()

    rows = [
        models.ProcessSnapshot(
            agent_id=agent_id,
            pid=p.pid,
            name=p.name,
            username=p.username,
            cpu_percent=p.cpu_percent,
            memory_percent=p.memory_percent,
        )
        for p in payload.processes
    ]
    db.add_all(rows)
    db.commit()

    for row in rows:
        db.refresh(row)
    return rows


@router.get("/{agent_id}/processes", response_model=list[schemas.ProcessOut])
def get_processes(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(models.Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")

    return (
        db.query(models.ProcessSnapshot)
        .filter(models.ProcessSnapshot.agent_id == agent_id)
        .order_by(models.ProcessSnapshot.cpu_percent.desc())
        .all()
    )

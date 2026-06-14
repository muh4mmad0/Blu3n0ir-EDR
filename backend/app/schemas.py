"""Pydantic schemas used for API request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import AgentStatus, Severity


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


class AgentRegister(BaseModel):
    hostname: str
    os: Optional[str] = None
    os_version: Optional[str] = None
    ip_address: Optional[str] = None


class AgentHeartbeat(BaseModel):
    cpu_percent: Optional[float] = None
    ram_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None
    ip_address: Optional[str] = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hostname: str
    os: Optional[str] = None
    os_version: Optional[str] = None
    ip_address: Optional[str] = None
    status: AgentStatus
    last_seen: datetime
    registered_at: datetime
    cpu_percent: Optional[float] = None
    ram_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None


# ---------------------------------------------------------------------------
# Processes
# ---------------------------------------------------------------------------


class ProcessIn(BaseModel):
    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None


class ProcessSnapshotIn(BaseModel):
    processes: list[ProcessIn]


class ProcessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    captured_at: datetime


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


class AlertIn(BaseModel):
    alert_type: str
    severity: Severity = Severity.info
    message: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: str
    alert_type: str
    severity: Severity
    message: str
    resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

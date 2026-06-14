"""SQLAlchemy ORM models for the Mini EDR backend."""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


def generate_id() -> str:
    return uuid.uuid4().hex


class AgentStatus(str, enum.Enum):
    online = "online"
    offline = "offline"


class Severity(str, enum.Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Agent(Base):
    """A monitored endpoint."""

    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_id)
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    status = Column(Enum(AgentStatus), default=AgentStatus.offline, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    cpu_percent = Column(Float, nullable=True)
    ram_percent = Column(Float, nullable=True)
    uptime_seconds = Column(Integer, nullable=True)

    processes = relationship(
        "ProcessSnapshot", back_populates="agent", cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="agent", cascade="all, delete-orphan")
    file_records = relationship(
        "FileRecord", back_populates="agent", cascade="all, delete-orphan"
    )


class ProcessSnapshot(Base):
    """A single process entry from the most recent snapshot uploaded by an agent.

    Each upload replaces the agent's previous snapshot rows (see
    routers/processes.py), so this table always reflects "what's running now"
    rather than a full history.
    """

    __tablename__ = "process_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)

    pid = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("Agent", back_populates="processes")


class Alert(Base):
    """A security or operational event raised by an agent or the backend."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)

    alert_type = Column(String, nullable=False)  # e.g. "file_integrity", "process"
    severity = Column(Enum(Severity), default=Severity.info, nullable=False)
    message = Column(Text, nullable=False)

    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("Agent", back_populates="alerts")


class FileRecord(Base):
    """Last-known hash of a file being watched for integrity changes."""

    __tablename__ = "file_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)

    path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("Agent", back_populates="file_records")

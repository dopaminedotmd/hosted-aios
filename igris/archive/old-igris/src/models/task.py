"""
Task contracts for agent delegation in Commander Igris.

Every task passes through the central Contract Validator before dispatch.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """A unit of work dispatched to an agent."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_id: Optional[str] = Field(default=None, description="Assigned agent ID")
    description: str = Field(..., min_length=1, description="What to do")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    contract_type: str = Field(default="patch", description="e.g. patch, scaffold, test, review")
    target_files: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    def mark_assigned(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.status = TaskStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()

    def mark_completed(self, result: dict[str, Any]) -> None:
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.result = {"error": error}
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()

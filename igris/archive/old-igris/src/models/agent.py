"""
Agent lifecycle models for Commander Igris.

Agent ranks:
  Level 0 (Spawned)  — fresh agent, isolated Docker sandbox, basic tools only
  B-Rank (Task Ready) — passed JSON validation + basic tests; can do surgical patches
  A-Rank (Autonomous)  — trained in Active Idle Mode, passed synthetic tests, fully trusted
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentRank(str, Enum):
    LEVEL_0 = "level_0"   # Spawned — fresh, untested
    B_RANK = "b_rank"     # Task Ready — validated, trusted for patches
    A_RANK = "a_rank"     # Autonomous Expert — full trust


class AgentStatus(str, Enum):
    IDLE = "idle"
    TRAINING = "training"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class Agent(BaseModel):
    """Core agent entity tracked by the Igris orchestrator."""

    agent_id: str = Field(..., description="Unique agent identifier, e.g. 'agent-python-01'")
    name: str = Field(..., description="Human-readable agent name")
    rank: AgentRank = Field(default=AgentRank.LEVEL_0, description="Current agent rank")
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    language: str = Field(default="python", description="Primary language: python, node, go")
    container_id: Optional[str] = Field(default=None, description="Docker container ID")
    spawned_at: datetime = Field(default_factory=datetime.utcnow)
    promoted_at: Optional[datetime] = Field(default=None)
    tasks_completed: int = Field(default=0)
    tests_passed: int = Field(default=0)
    tests_failed: int = Field(default=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def can_promote_to_b(self) -> bool:
        """B-Rank eligibility: at least 5 tasks completed, 80%+ success rate."""
        return (
            self.rank == AgentRank.LEVEL_0
            and self.tasks_completed >= 5
            and self.success_rate >= 0.8
        )

    @property
    def can_promote_to_a(self) -> bool:
        """A-Rank eligibility: at least 20 tasks completed, 90%+ success rate."""
        return (
            self.rank == AgentRank.B_RANK
            and self.tasks_completed >= 20
            and self.success_rate >= 0.9
        )

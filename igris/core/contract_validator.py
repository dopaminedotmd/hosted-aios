"""
Central Contract Validator for Commander Igris.

ALL inter-agent communication MUST pass through this validator.
Rejects any message that does not conform to a registered contract schema.

Architecture:
  Incoming JSON → Schema Registry lookup → Pydantic validation → pass/fail
  Failed messages are logged, rejected, and optionally returned with error details.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, ValidationError, field_validator


# ─── Contract Envelope ────────────────────────────────────────────────────────

class ContractType(str, Enum):
    """All registered contract types in the Igris system."""
    AGENT_SPAWN_REQUEST = "agent_spawn_request"
    AGENT_SPAWN_RESPONSE = "agent_spawn_response"
    AGENT_STATUS_UPDATE = "agent_status_update"
    AGENT_PROMOTE = "agent_promote"
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    GPU_ALLOCATION_REQUEST = "gpu_allocation_request"
    GPU_ALLOCATION_RESPONSE = "gpu_allocation_response"
    HEARTBEAT = "heartbeat"


class ContractEnvelope(BaseModel):
    """Every message in Igris is wrapped in a ContractEnvelope.

    The envelope carries routing metadata; the payload is contract-specific.
    """

    envelope_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    contract_type: ContractType
    sender_id: str = Field(..., min_length=1, description="Agent or component sending this")
    receiver_id: str = Field(default="igris-core", description="Target component")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(..., description="Contract-specific data")
    version: str = Field(default="1.0.0")

    @field_validator("payload")
    @classmethod
    def payload_must_not_be_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("payload must not be empty")
        return v


# ─── Individual Contracts ─────────────────────────────────────────────────────

class AgentSpawnRequest(BaseModel):
    """Request to spawn a new Docker-based agent."""
    name: str = Field(..., min_length=1, max_length=64)
    language: str = Field(default="python", pattern=r"^(python|node|go)$")
    tools: list[str] = Field(default_factory=list, description="Tool names the agent needs")
    base_image: str = Field(default="python:3.11-slim")
    memory_limit_mb: int = Field(default=512, ge=128, le=4096)
    cpu_limit: float = Field(default=1.0, ge=0.5, le=4.0)


class AgentSpawnResponse(BaseModel):
    """Response after attempting to spawn an agent."""
    success: bool
    agent_id: Optional[str] = None
    container_id: Optional[str] = None
    error: Optional[str] = None


class AgentStatusUpdate(BaseModel):
    """Periodic status report from an agent to Igris core."""
    agent_id: str
    status: str = Field(..., pattern=r"^(idle|training|busy|error|terminated)$")
    current_task_id: Optional[str] = None
    vram_used_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    uptime_seconds: Optional[float] = None


class AgentPromote(BaseModel):
    """Command to promote an agent to a higher rank."""
    agent_id: str
    from_rank: str
    to_rank: str = Field(..., pattern=r"^(level_0|b_rank|a_rank)$")
    reason: str = Field(..., min_length=1)


class TaskAssign(BaseModel):
    """Dispatch a task to a specific agent."""
    task_id: str
    agent_id: str
    description: str = Field(..., min_length=1)
    contract_type: str = Field(default="patch")
    target_files: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    deadline_seconds: Optional[int] = Field(default=None, ge=60)


class TaskResult(BaseModel):
    """Agent reports task completion or failure."""
    task_id: str
    agent_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    files_changed: list[str] = Field(default_factory=list)
    tests_passed: int = Field(default=0)
    tests_failed: int = Field(default=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)


class GPUAllocationRequest(BaseModel):
    """Request VRAM allocation for a component."""
    component: str = Field(..., min_length=1)
    requested_gb: float = Field(..., gt=0.0, le=24.0)
    min_gb: float = Field(default=0.0, ge=0.0)
    max_gb: float = Field(default=24.0, le=24.0)


class GPUAllocationResponse(BaseModel):
    """Response to VRAM allocation request."""
    approved: bool
    allocated_gb: float = Field(default=0.0)
    free_remaining_gb: float = Field(default=0.0)
    reason: Optional[str] = None


class Heartbeat(BaseModel):
    """Lightweight liveness ping."""
    agent_id: str
    sequence: int = Field(default=0, ge=0)


# ─── Schema Registry ──────────────────────────────────────────────────────────

# Maps ContractType → Pydantic model for payload validation.
SCHEMA_REGISTRY: dict[ContractType, Type[BaseModel]] = {
    ContractType.AGENT_SPAWN_REQUEST: AgentSpawnRequest,
    ContractType.AGENT_SPAWN_RESPONSE: AgentSpawnResponse,
    ContractType.AGENT_STATUS_UPDATE: AgentStatusUpdate,
    ContractType.AGENT_PROMOTE: AgentPromote,
    ContractType.TASK_ASSIGN: TaskAssign,
    ContractType.TASK_RESULT: TaskResult,
    ContractType.GPU_ALLOCATION_REQUEST: GPUAllocationRequest,
    ContractType.GPU_ALLOCATION_RESPONSE: GPUAllocationResponse,
    ContractType.HEARTBEAT: Heartbeat,
}


# ─── Validator ────────────────────────────────────────────────────────────────

class ValidationResult(BaseModel):
    """Result of a contract validation attempt."""
    valid: bool
    envelope: Optional[ContractEnvelope] = None
    payload_model: Optional[BaseModel] = None
    errors: list[str] = Field(default_factory=list)


class ContractValidator:
    """Singleton validator for all Igris inter-agent messages.

    Usage:
        validator = ContractValidator()
        result = validator.validate(raw_json_string)
        if result.valid:
            dispatch(result.envelope, result.payload_model)
    """

    def validate(self, raw: str | bytes | dict) -> ValidationResult:
        """Validate a raw message against the schema registry.

        Flow:
          1. Parse JSON → dict
          2. Validate outer ContractEnvelope
          3. Look up contract_type in SCHEMA_REGISTRY
          4. Validate payload against the registered Pydantic model
          5. Return ValidationResult
        """
        errors: list[str] = []

        # Step 1: Parse
        if isinstance(raw, (str, bytes)):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                return ValidationResult(valid=False, errors=[f"JSON parse error: {e}"])
        elif isinstance(raw, dict):
            data = raw
        else:
            return ValidationResult(valid=False, errors=[f"Expected str, bytes, or dict, got {type(raw).__name__}"])

        # Step 2: Validate envelope
        try:
            envelope = ContractEnvelope(**data)
        except ValidationError as e:
            return ValidationResult(valid=False, errors=[f"Envelope validation failed: {e}"])

        # Step 3 + 4: Lookup + validate payload
        schema = SCHEMA_REGISTRY.get(envelope.contract_type)
        if schema is None:
            return ValidationResult(
                valid=False,
                envelope=envelope,
                errors=[f"Unknown contract_type: {envelope.contract_type.value}"],
            )

        try:
            payload_model = schema(**envelope.payload)
        except ValidationError as e:
            return ValidationResult(
                valid=False,
                envelope=envelope,
                errors=[f"Payload validation failed for {envelope.contract_type.value}: {e}"],
            )

        return ValidationResult(valid=True, envelope=envelope, payload_model=payload_model)

    def build_envelope(
        self,
        contract_type: ContractType,
        sender_id: str,
        payload: dict[str, Any],
        receiver_id: str = "igris-core",
    ) -> ContractEnvelope:
        """Build a valid envelope (raises ValidationError if payload is invalid)."""
        schema = SCHEMA_REGISTRY[contract_type]
        schema(**payload)  # pre-validate payload
        return ContractEnvelope(
            contract_type=contract_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=payload,
        )

    def to_json(self, envelope: ContractEnvelope) -> str:
        """Serialize a ContractEnvelope to JSON string for transport."""
        return envelope.model_dump_json(indent=2)

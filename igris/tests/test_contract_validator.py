"""
Tests for Contract Validator — the central validation layer of Igris.

Covers:
  - All 8 contract types
  - Valid and invalid payloads
  - Edge cases (empty payload, missing fields, wrong types)
  - Envelope building and serialization
"""

import json

import pytest

from igris.core.contract_validator import (
    ContractValidator,
    ContractType,
    ContractEnvelope,
    AgentSpawnRequest,
    AgentSpawnResponse,
    AgentStatusUpdate,
    AgentPromote,
    TaskAssign,
    TaskResult,
    GPUAllocationRequest,
    GPUAllocationResponse,
    Heartbeat,
    SCHEMA_REGISTRY,
)


@pytest.fixture
def validator():
    return ContractValidator()


# ─── Envelope tests ───────────────────────────────────────────────────────────

class TestContractEnvelope:
    def test_valid_envelope(self):
        env = ContractEnvelope(
            contract_type=ContractType.HEARTBEAT,
            sender_id="agent-001",
            payload={"agent_id": "agent-001", "sequence": 0},
        )
        assert env.contract_type == ContractType.HEARTBEAT
        assert len(env.envelope_id) == 12

    def test_empty_payload_rejected(self):
        with pytest.raises(ValueError, match="payload must not be empty"):
            ContractEnvelope(
                contract_type=ContractType.HEARTBEAT,
                sender_id="agent-001",
                payload={},
            )

    def test_missing_sender_rejected(self):
        with pytest.raises(ValueError):
            ContractEnvelope(
                contract_type=ContractType.HEARTBEAT,
                sender_id="",  # empty — min_length=1
                payload={"agent_id": "x", "sequence": 0},
            )


# ─── Individual contract tests ────────────────────────────────────────────────

class TestAgentSpawnRequest:
    def test_valid(self):
        c = AgentSpawnRequest(name="test-agent", language="python")
        assert c.name == "test-agent"
        assert c.language == "python"

    def test_invalid_language(self):
        with pytest.raises(ValueError):
            AgentSpawnRequest(name="x", language="rust")

    def test_memory_limit_bounds(self):
        with pytest.raises(ValueError):
            AgentSpawnRequest(name="x", memory_limit_mb=64)  # below 128


class TestAgentPromote:
    def test_valid(self):
        c = AgentPromote(agent_id="a1", from_rank="level_0", to_rank="b_rank", reason="deserves it")
        assert c.to_rank == "b_rank"

    def test_invalid_rank(self):
        with pytest.raises(ValueError):
            AgentPromote(agent_id="a1", from_rank="level_0", to_rank="s_rank", reason="nope")


class TestTaskAssign:
    def test_valid(self):
        c = TaskAssign(task_id="t1", agent_id="a1", description="Fix bug")
        assert c.priority == "medium"

    def test_empty_description(self):
        with pytest.raises(ValueError):
            TaskAssign(task_id="t1", agent_id="a1", description="")


class TestTaskResult:
    def test_success(self):
        c = TaskResult(task_id="t1", agent_id="a1", success=True, tests_passed=5, duration_seconds=3.2)
        assert c.success is True

    def test_failure(self):
        c = TaskResult(task_id="t1", agent_id="a1", success=False, error="timeout", tests_failed=1)
        assert c.error == "timeout"


class TestGPUAllocation:
    def test_valid_request(self):
        c = GPUAllocationRequest(component="test-model", requested_gb=2.0)
        assert c.requested_gb == 2.0

    def test_negative_gb_rejected(self):
        with pytest.raises(ValueError):
            GPUAllocationRequest(component="x", requested_gb=-1.0)

    def test_exceeds_vram_rejected(self):
        with pytest.raises(ValueError):
            GPUAllocationRequest(component="x", requested_gb=25.0)


class TestHeartbeat:
    def test_valid(self):
        c = Heartbeat(agent_id="a1", sequence=42)
        assert c.sequence == 42


# ─── Validator integration tests ──────────────────────────────────────────────

class TestValidatorIntegration:
    def test_validate_valid_heartbeat(self, validator):
        msg = {
            "contract_type": "heartbeat",
            "sender_id": "agent-001",
            "payload": {"agent_id": "agent-001", "sequence": 1},
        }
        result = validator.validate(msg)
        assert result.valid is True
        assert isinstance(result.payload_model, Heartbeat)

    def test_validate_valid_spawn(self, validator):
        msg = {
            "contract_type": "agent_spawn_request",
            "sender_id": "igris-core",
            "payload": {"name": "new-agent", "language": "python", "tools": ["read_file"]},
        }
        result = validator.validate(msg)
        assert result.valid is True
        assert isinstance(result.payload_model, AgentSpawnRequest)

    def test_validate_invalid_json(self, validator):
        result = validator.validate("not json at all")
        assert result.valid is False
        assert "JSON parse error" in result.errors[0]

    def test_validate_unknown_contract_type(self, validator):
        msg = {
            "contract_type": "nonexistent",
            "sender_id": "x",
            "payload": {"x": 1},
        }
        result = validator.validate(msg)
        assert result.valid is False
        # Pydantic catches the invalid enum at the envelope level
        assert any(
            "contract_type" in err for err in result.errors
        ), f"Expected contract_type error, got: {result.errors}"

    def test_validate_bad_payload(self, validator):
        msg = {
            "contract_type": "task_assign",
            "sender_id": "x",
            "payload": {"task_id": "t1"},  # missing agent_id and description
        }
        result = validator.validate(msg)
        assert result.valid is False
        assert "Payload validation failed" in result.errors[0]

    def test_validate_from_json_string(self, validator):
        raw = json.dumps({
            "contract_type": "heartbeat",
            "sender_id": "agent-001",
            "payload": {"agent_id": "agent-001", "sequence": 0},
        })
        result = validator.validate(raw)
        assert result.valid is True

    def test_build_envelope(self, validator):
        env = validator.build_envelope(
            ContractType.HEARTBEAT,
            "agent-001",
            {"agent_id": "agent-001", "sequence": 5},
        )
        assert env.contract_type == ContractType.HEARTBEAT
        assert env.sender_id == "agent-001"

    def test_build_envelope_invalid_payload_raises(self, validator):
        with pytest.raises(ValueError):
            validator.build_envelope(
                ContractType.HEARTBEAT,
                "agent-001",
                {"wrong_field": 1},  # missing required fields
            )

    def test_to_json_roundtrip(self, validator):
        env = validator.build_envelope(
            ContractType.HEARTBEAT,
            "agent-x",
            {"agent_id": "agent-x", "sequence": 1},
        )
        json_str = validator.to_json(env)
        parsed = json.loads(json_str)
        assert parsed["contract_type"] == "heartbeat"
        assert parsed["sender_id"] == "agent-x"


# ─── Schema registry completeness ─────────────────────────────────────────────

def test_all_contract_types_registered():
    """Every ContractType enum value must have a schema."""
    for ct in ContractType:
        assert ct in SCHEMA_REGISTRY, f"Missing schema for {ct.value}"

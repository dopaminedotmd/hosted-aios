"""
CLI entry point for Commander Igris.

Usage:
  python -m igris.cli.main          # Start orchestrator loop
  python -m igris.cli.main status   # Print system status
  python -m igris.cli.main validate # Validate all contracts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the igris package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def cmd_run(data_dir: str = "data", interval: int = 30) -> None:
    """Start the Igris orchestrator loop."""
    from igris.core.orchestrator import IgrisOrchestrator

    igris = IgrisOrchestrator(data_dir=Path(data_dir))
    igris.run_loop(interval_s=interval)


def cmd_status(data_dir: str = "data") -> None:
    """Print current system status and exit."""
    from igris.core.orchestrator import IgrisOrchestrator

    igris = IgrisOrchestrator(data_dir=Path(data_dir))
    igris._print_status()
    print()

    print("Agents:")
    for agent in igris.agents.values():
        print(f"  {agent.agent_id}: rank={agent.rank.value} status={agent.status.value} "
              f"tasks={agent.tasks_completed} success={agent.success_rate:.0%}")

    print(f"\nTasks ({len(igris.tasks)} total):")
    for task in igris.tasks.values():
        print(f"  {task.task_id}: [{task.priority.value}] {task.status.value} — {task.description[:60]}")

    print(f"\nEvent log: {len(igris.event_log)} entries")


def cmd_validate() -> None:
    """Run validation against all contract schemas."""
    from igris.core.contract_validator import ContractValidator, ContractType

    validator = ContractValidator()
    print("Contract Schema Registry:")
    print("─" * 40)

    test_payloads = {
        ContractType.AGENT_SPAWN_REQUEST: {
            "contract_type": "agent_spawn_request",
            "sender_id": "test",
            "payload": {"name": "test-agent", "language": "python"},
        },
        ContractType.TASK_ASSIGN: {
            "contract_type": "task_assign",
            "sender_id": "test",
            "payload": {
                "task_id": "task-0001",
                "agent_id": "agent-001",
                "description": "Test task",
            },
        },
        ContractType.AGENT_PROMOTE: {
            "contract_type": "agent_promote",
            "sender_id": "test",
            "payload": {
                "agent_id": "agent-001",
                "from_rank": "level_0",
                "to_rank": "b_rank",
                "reason": "test promotion",
            },
        },
        ContractType.HEARTBEAT: {
            "contract_type": "heartbeat",
            "sender_id": "test",
            "payload": {"agent_id": "agent-001", "sequence": 0},
        },
    }

    all_ok = True
    for ct, payload in test_payloads.items():
        result = validator.validate(payload)
        status = "PASS" if result.valid else "FAIL"
        if not result.valid:
            all_ok = False
        print(f"  {ct.value:30s} → {status}")
        if result.errors:
            for err in result.errors:
                print(f"    Error: {err[:100]}")

    print("─" * 40)
    print(f"Overall: {'ALL PASSED' if all_ok else 'SOME FAILED'}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m igris.cli.main [run|status|validate]")
        sys.exit(1)

    cmd = sys.argv[1]
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"

    if cmd == "run":
        cmd_run(data_dir=data_dir)
    elif cmd == "status":
        cmd_status(data_dir=data_dir)
    elif cmd == "validate":
        cmd_validate()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

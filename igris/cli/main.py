"""
CLI entry point for Commander Igris.

Usage:
  python -m igris.cli.main run [data_dir]       # Start orchestrator loop
  python -m igris.cli.main status [data_dir]    # Print system status
  python -m igris.cli.main validate             # Validate all contracts
  python -m igris.cli.main map <repo_path>      # Scan repo with Cartographer
  python -m igris.cli.main map-incremental <repo_path>  # Incremental scan
  python -m igris.cli.main idle [threshold_min] # Start idle monitor
"""

from __future__ import annotations

import json
import sys
import time
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


# ─── Phase 0: Cartographer commands ──────────────────────────────────────────

def cmd_map(repo_path: str, full: bool = False) -> None:
    """Scan a repo and print the Repo-Map summary."""
    from igris.cartographer import RepoCartographer

    ctg = RepoCartographer(repo_path)
    t0 = time.time()
    repo_map = ctg.scan(force_full=full)
    elapsed = time.time() - t0

    print(f"Repo: {repo_map.repo_root}")
    print(f"Files: {repo_map.total_files}")
    print(f"Symbols: {repo_map.total_symbols}")
    print(f"Languages: {dict(repo_map.languages)}")
    print(f"Scan time: {elapsed:.2f}s ({'full' if full else 'incremental'})")
    print()

    # Show top files by symbol count
    top_files = sorted(repo_map.files.values(), key=lambda f: len(f.symbols), reverse=True)[:10]
    print("Top files by symbol count:")
    for entry in top_files:
        if entry.symbols:
            print(f"  {entry.path} ({entry.language}): {len(entry.symbols)} symbols")
            # Show first 3 symbols
            for sym in entry.symbols[:3]:
                print(f"    [{sym.kind}] {sym.name} (line {sym.line})")


def cmd_map_incremental(repo_path: str) -> None:
    """Incremental scan only."""
    cmd_map(repo_path, full=False)


def cmd_map_full(repo_path: str) -> None:
    """Full scan (ignore cache)."""
    cmd_map(repo_path, full=True)


# ─── Phase 0: Idle detection command ─────────────────────────────────────────

def cmd_idle(threshold_min: int = 15) -> None:
    """Start idle detector in foreground (Ctrl+C to stop)."""
    from igris.idle_detector import IdleDetector

    def on_idle():
        print("\n[IDLE] No activity for threshold — entering Active Idle Mode")
        print("[IDLE] GPU → 90% Igris, training agents...")

    def on_wake():
        print("\n[WAKE] Activity detected — freezing, saving state, releasing VRAM")

    detector = IdleDetector(
        threshold_s=threshold_min * 60,
        on_idle=on_idle,
        on_wake=on_wake,
    )
    detector.start(check_interval_s=2.0)

    print(f"Idle detector running. Threshold: {threshold_min} min.")
    print("Every keypress = activity. Press Ctrl+C to stop.")
    print(f"State: {detector.state.value}")

    try:
        while True:
            time.sleep(2)
            status = detector.status_dict()
            idle_s = status["idle_seconds"]
            state = status["state"]
            if idle_s > 0 and int(idle_s) % 10 == 0:
                print(f"  idle: {idle_s:.0f}s | state: {state}")
            # Simulate activity detection (in real CLI, this would hook stdin)
    except KeyboardInterrupt:
        print("\nStopped.")
        detector.stop()


# ─── Main ────────────────────────────────────────────────────────────────────

USAGE = """Usage: python -m igris.cli.main <command> [args]

Commands:
  run [data_dir]             Start orchestrator loop
  status [data_dir]          Print system status
  validate                   Validate all contracts
  map <repo_path>            Scan repo with Cartographer (incremental)
  map-full <repo_path>       Full repo scan (ignore cache)
  idle [threshold_min]       Start idle monitor (default 15 min)
"""


def main() -> None:
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "run":
        data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"
        cmd_run(data_dir=data_dir)
    elif cmd == "status":
        data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"
        cmd_status(data_dir=data_dir)
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "map":
        if len(sys.argv) < 3:
            print("Usage: python -m igris.cli.main map <repo_path>")
            sys.exit(1)
        cmd_map(sys.argv[2])
    elif cmd == "map-full":
        if len(sys.argv) < 3:
            print("Usage: python -m igris.cli.main map-full <repo_path>")
            sys.exit(1)
        cmd_map_full(sys.argv[2])
    elif cmd == "idle":
        threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        cmd_idle(threshold)
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()

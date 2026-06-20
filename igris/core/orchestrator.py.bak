"""
Commander Igris — Main Orchestrator.

Implements the core loop:
  Observe → Evaluate → Provision → Deploy

The orchestrator is the central nervous system:
  - Reads agent registry, task queue, GPU state
  - Calls the router (8B model) for decisions
  - Validates all decisions through ContractValidator
  - Executes: spawn agents, assign tasks, promote agents

This is a SINGLETON — only one Igris instance runs per host.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from igris.core.contract_validator import (
    ContractType,
    ContractValidator,
    ContractEnvelope,
    AgentSpawnRequest,
    AgentSpawnResponse,
    TaskAssign,
    AgentPromote,
    AgentStatusUpdate,
)
from igris.core.gpu_manager import GPUManager
from igris.models.agent import Agent, AgentRank, AgentStatus
from igris.models.task import Task, TaskPriority, TaskStatus


# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_LOOP_INTERVAL_S = 30           # How often the loop runs (seconds)
ACTIVE_IDLE_THRESHOLD_S = 15 * 60      # 15 minutes → Active Idle Mode


class IgrisOrchestrator:
    """Central orchestrator for Commander Igris multi-agent system.

    Usage:
        igris = IgrisOrchestrator(data_dir=Path("C:/LLM/igris/data"))
        igris.run_loop()  # blocking
    """

    def __init__(self, data_dir: Path | str = Path("data")) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.validator = ContractValidator()
        self.gpu = GPUManager()

        # In-memory registries (backed by JSON on disk for persistence)
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self.event_log: list[dict[str, Any]] = []

        # Router state
        self.last_human_input: Optional[datetime] = None
        self.active_idle: bool = False
        self.loop_count: int = 0

        self._load_state()

    # ─── State Persistence ─────────────────────────────────────────────────

    def _load_state(self) -> None:
        """Load agent registry and task queue from disk."""
        agents_file = self.data_dir / "agents.json"
        tasks_file = self.data_dir / "tasks.json"

        if agents_file.exists():
            raw = json.loads(agents_file.read_text())
            for a_data in raw:
                agent = Agent(**a_data)
                self.agents[agent.agent_id] = agent

        if tasks_file.exists():
            raw = json.loads(tasks_file.read_text())
            for t_data in raw:
                task = Task(**t_data)
                self.tasks[task.task_id] = task

    def _save_state(self) -> None:
        """Persist agent registry and task queue to disk."""
        agents_data = [a.model_dump(mode="json") for a in self.agents.values()]
        tasks_data = [t.model_dump(mode="json") for t in self.tasks.values()]

        (self.data_dir / "agents.json").write_text(json.dumps(agents_data, indent=2, default=str))
        (self.data_dir / "tasks.json").write_text(json.dumps(tasks_data, indent=2, default=str))

    # ─── Observe Phase ────────────────────────────────────────────────────

    def observe(self) -> dict[str, Any]:
        """Gather current system state: agents, tasks, GPU, backlog."""
        snap = self.gpu.snapshot()
        oom = self.gpu.check_oom_risk()

        idle_count = sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE)
        busy_count = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
        error_count = sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents_total": len(self.agents),
            "agents_idle": idle_count,
            "agents_busy": busy_count,
            "agents_error": error_count,
            "pending_tasks": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "vram_free_gb": snap.free_gb,
            "vram_used_gb": snap.used_gb,
            "gpu_util_pct": snap.utilization_pct,
            "oom_risk": oom,
            "active_idle_mode": self.active_idle,
            "loop_count": self.loop_count,
        }

    # ─── Evaluate Phase ───────────────────────────────────────────────────

    def evaluate(self, router_output: str) -> dict[str, Any]:
        """Parse router model output into an actionable decision.

        The router (Llama-3.1-8B) outputs raw JSON. We parse and validate it.
        In production, this calls the actual LLM; for now, we parse pre-rendered JSON.
        """
        try:
            # Strip markdown fences if the model wraps in ```json
            cleaned = router_output.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("\n", 1)[0]

            decision = json.loads(cleaned)
            action = decision.get("action", "noop")

            if action not in ("spawn", "assign", "promote", "train", "noop"):
                self._log("evaluate", f"Unknown action: {action}", "warn")
                return {"action": "noop", "reason": f"unknown action: {action}"}

            return decision

        except json.JSONDecodeError as e:
            self._log("evaluate", f"Router JSON parse error: {e}", "error")
            return {"action": "noop", "reason": "json_parse_error"}

    # ─── Provision Phase ──────────────────────────────────────────────────

    def provision(self, decision: dict[str, Any]) -> Optional[ContractEnvelope]:
        """Convert a router decision into a validated ContractEnvelope.

        Returns None if the decision cannot be actioned (invalid, blocked, etc.).
        """
        action = decision["action"]

        if action == "spawn":
            return self._provision_spawn(decision)

        elif action == "assign":
            return self._provision_assign(decision)

        elif action == "promote":
            return self._provision_promote(decision)

        elif action == "train":
            return self._provision_train(decision)

        elif action == "noop":
            self._log("provision", "No operation — system stable")
            return None

        return None

    def _provision_spawn(self, decision: dict) -> Optional[ContractEnvelope]:
        """Validate and build a spawn contract."""
        name = decision.get("name", f"agent-{len(self.agents)+1:03d}")
        language = decision.get("language", "python")
        reason = decision.get("reason", "router requested")

        # Check VRAM budget
        if not self.gpu.can_allocate(f"agent-{name}", 0.5):
            self._log("provision", f"VRAM budget exceeded, cannot spawn {name}", "warn")
            return None

        try:
            return self.validator.build_envelope(
                contract_type=ContractType.AGENT_SPAWN_REQUEST,
                sender_id="igris-core",
                payload={
                    "name": name,
                    "language": language,
                    "tools": ["read_file", "write_file", "terminal", "search_files"],
                },
            )
        except Exception as e:
            self._log("provision", f"Spawn contract build failed: {e}", "error")
            return None

    def _provision_assign(self, decision: dict) -> Optional[ContractEnvelope]:
        """Validate and build a task assignment contract."""
        task_id = decision.get("task_id", "")
        agent_id = decision.get("agent_id", "")
        description = decision.get("description", "")
        priority = decision.get("priority", "medium")

        if task_id not in self.tasks:
            self._log("provision", f"Unknown task_id: {task_id}", "warn")
            return None
        if agent_id not in self.agents:
            self._log("provision", f"Unknown agent_id: {agent_id}", "warn")
            return None

        agent = self.agents[agent_id]
        if agent.status in (AgentStatus.BUSY, AgentStatus.ERROR):
            self._log("provision", f"Agent {agent_id} is {agent.status.value}, cannot assign", "warn")
            return None
        if agent.rank == AgentRank.LEVEL_0:
            self._log("provision", f"Agent {agent_id} is Level 0 — must reach B-Rank first", "warn")
            return None

        try:
            return self.validator.build_envelope(
                contract_type=ContractType.TASK_ASSIGN,
                sender_id="igris-core",
                receiver_id=agent_id,
                payload={
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "description": description,
                    "priority": priority,
                },
            )
        except Exception as e:
            self._log("provision", f"Assign contract build failed: {e}", "error")
            return None

    def _provision_promote(self, decision: dict) -> Optional[ContractEnvelope]:
        """Validate and build a promotion contract."""
        agent_id = decision.get("agent_id", "")
        to_rank = decision.get("to_rank", "")
        reason = decision.get("reason", "router requested")

        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        from_rank = agent.rank.value

        if to_rank == "b_rank" and not agent.can_promote_to_b:
            self._log("provision", f"Agent {agent_id} not eligible for B-Rank", "warn")
            return None
        if to_rank == "a_rank" and not agent.can_promote_to_a:
            self._log("provision", f"Agent {agent_id} not eligible for A-Rank", "warn")
            return None

        try:
            return self.validator.build_envelope(
                contract_type=ContractType.AGENT_PROMOTE,
                sender_id="igris-core",
                receiver_id=agent_id,
                payload={
                    "agent_id": agent_id,
                    "from_rank": from_rank,
                    "to_rank": to_rank,
                    "reason": reason,
                },
            )
        except Exception as e:
            self._log("provision", f"Promote contract build failed: {e}", "error")
            return None

    def _provision_train(self, decision: dict) -> Optional[ContractEnvelope]:
        """Put an idle agent into training mode."""
        agent_id = decision.get("agent_id", "")
        focus = decision.get("focus", "general")

        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        if agent.status != AgentStatus.IDLE:
            return None

        agent.status = AgentStatus.TRAINING
        self._log("provision", f"Agent {agent_id} → TRAINING (focus: {focus})")
        return None  # Training is a state change, not a dispatched contract

    # ─── Deploy Phase ─────────────────────────────────────────────────────

    def deploy(self, envelope: ContractEnvelope) -> bool:
        """Execute a validated contract.

        Currently simulated — Phase 2 will dispatch to Docker containers.
        """
        ct = envelope.contract_type

        if ct == ContractType.AGENT_SPAWN_REQUEST:
            return self._deploy_spawn(envelope)

        elif ct == ContractType.TASK_ASSIGN:
            return self._deploy_assign(envelope)

        elif ct == ContractType.AGENT_PROMOTE:
            return self._deploy_promote(envelope)

        self._log("deploy", f"Unhandled contract type: {ct.value}", "warn")
        return False

    def _deploy_spawn(self, envelope: ContractEnvelope) -> bool:
        """Spawn a new agent (simulated — Phase 2 adds Docker)."""
        payload = envelope.payload
        agent_id = f"agent-{payload['language']}-{len(self.agents)+1:03d}"

        agent = Agent(
            agent_id=agent_id,
            name=payload["name"],
            language=payload["language"],
            rank=AgentRank.LEVEL_0,
            status=AgentStatus.IDLE,
        )
        self.agents[agent_id] = agent
        self.gpu.allocate(agent_id, 0.5)  # reserve 0.5 GB for new agent

        self._log("deploy", f"Spawned {agent_id} ({payload['language']}) — Level 0")
        self._save_state()
        return True

    def _deploy_assign(self, envelope: ContractEnvelope) -> bool:
        """Assign a task to an agent."""
        payload = envelope.payload
        task = self.tasks.get(payload["task_id"])
        agent = self.agents.get(payload["agent_id"])

        if not task or not agent:
            return False

        task.mark_assigned(payload["agent_id"])
        agent.status = AgentStatus.BUSY

        self._log("deploy", f"Task {task.task_id} → {agent.agent_id}")
        self._save_state()
        return True

    def _deploy_promote(self, envelope: ContractEnvelope) -> bool:
        """Promote an agent to the next rank."""
        payload = envelope.payload
        agent = self.agents.get(payload["agent_id"])
        if not agent:
            return False

        new_rank = AgentRank(payload["to_rank"])
        old_rank = agent.rank
        agent.rank = new_rank
        agent.promoted_at = datetime.utcnow()

        self._log("deploy", f"Agent {agent.agent_id}: {old_rank.value} → {new_rank.value}")
        self._save_state()
        return True

    # ─── Main Loop ────────────────────────────────────────────────────────

    def run_loop(self, router_fn=None, interval_s: int = DEFAULT_LOOP_INTERVAL_S,
                 verbose: bool = True) -> None:
        """Run the Observe → Evaluate → Provision → Deploy loop.

        Args:
            router_fn: Callable that takes (agents, tasks, vram, oom) and returns a
                       router JSON string. If None, runs in simulation mode.
            interval_s: Seconds between loop iterations.
            verbose: If True (default), print real-time thoughts every loop.
        """
        self._log("orchestrator", "Igris loop started")

        sep = "═" * 60
        thin = "─" * 60

        print(f"\n{sep}")
        print("  COMMANDER IGRIS — Realtidsövervakning")
        print(f"{sep}")
        print(f"  Loop-intervall: {interval_s}s")
        print(f"  Active Idle:    {ACTIVE_IDLE_THRESHOLD_S // 60} min inaktivitet")
        print(f"  Agenter:        {len(self.agents)}")
        print(f"  Tasks:          {len(self.tasks)}")
        print(f"{sep}\n")

        try:
            while True:
                self.loop_count += 1

                # ── Observe ──
                obs = self.observe()
                snap = self.gpu.snapshot()

                if verbose:
                    print(f"{thin}")
                    print(f"  LOOP #{self.loop_count} — OBSERVE")
                    print(f"  ├─ Agenter: {obs['agents_total']} st "
                          f"(idle:{obs['agents_idle']} busy:{obs['agents_busy']} err:{obs['agents_error']})")
                    print(f"  ├─ Tasks pending: {obs['pending_tasks']}")
                    print(f"  ├─ GPU: {snap.used_gb:.1f}/{snap.total_gb:.1f} GB "
                          f"({snap.free_gb:.1f} GB fritt, {snap.temperature_c}°C)")
                    print(f"  └─ OOM-risk: {obs['oom_risk']['risk'].upper()}")

                # ── Evaluate (via router or simulation) ──
                if router_fn:
                    agents_list = [
                        {
                            "agent_id": a.agent_id,
                            "rank": a.rank.value,
                            "status": a.status.value,
                            "tasks_completed": a.tasks_completed,
                            "success_rate": a.success_rate,
                            "language": a.language,
                        }
                        for a in self.agents.values()
                    ]
                    tasks_list = [
                        {
                            "task_id": t.task_id,
                            "priority": t.priority.value,
                            "status": t.status.value,
                            "description": t.description,
                        }
                        for t in self.tasks.values()
                        if t.status == TaskStatus.PENDING
                    ]
                    vram = {
                        "free_gb": obs["vram_free_gb"],
                        "total_gb": self.gpu.hardware.gpu_vram_gb,
                    }
                    oom = obs["oom_risk"]
                    router_output = router_fn(agents_list, tasks_list, vram, oom)
                else:
                    router_output = self._simulate_router()

                decision = self.evaluate(router_output)

                # ── Show Igris "thinking" ──
                if verbose:
                    action = decision.get("action", "?")
                    reason = decision.get("reason", "")

                    action_labels = {
                        "spawn": "SPAWNA ny agent",
                        "assign": "TILLDELA task",
                        "promote": "BEFORDRA agent",
                        "train": "TRÄNA agent",
                        "noop": "INGEN ÅTGÄRD",
                    }
                    label = action_labels.get(action, action.upper())

                    print(f"  │")
                    print(f"  ├─ TÄNKER: {label}")
                    if reason:
                        print(f"  │  └─ {reason}")
                    if action == "spawn":
                        print(f"  │     Namn: {decision.get('name', '?')} "
                              f"({decision.get('language', '?')})")
                    elif action == "promote":
                        print(f"  │     Agent: {decision.get('agent_id', '?')} "
                              f"→ {decision.get('to_rank', '?')}")
                    elif action == "train":
                        print(f"  │     Agent: {decision.get('agent_id', '?')} "
                              f"fokus: {decision.get('focus', '?')}")

                # ── Provision ──
                envelope = self.provision(decision)

                # ── Deploy ──
                if envelope:
                    success = self.deploy(envelope)
                    status_icon = "✓" if success else "✗"
                    if verbose:
                        print(f"  │")
                        print(f"  └─ UTFÖR: {decision['action']} → {status_icon} {status_icon}")
                    else:
                        status = "OK" if success else "FAIL"
                        print(f"[loop {self.loop_count}] {decision['action']} → {status}")
                elif verbose:
                    ct = decision.get("action", "")
                    if ct != "noop":
                        print(f"  └─ BLOCKERAD: {decision.get('action', '')} kunde inte provisioneras")

                if verbose:
                    print(f"{thin}\n")

                time.sleep(interval_s)

        except KeyboardInterrupt:
            self._log("orchestrator", "Loop interrupted by user")
            self._save_state()
            print(f"\n{sep}")
            print("  Igris avslutad. State sparat.")
            print(f"{sep}\n")

    def _simulate_router(self) -> str:
        """Simulate router decisions when no LLM is connected.

        Auto-promotes eligible agents. Shows awareness of pending tasks.
        """
        # Count pending tasks by priority
        pending = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        critical = [t for t in pending if t.priority == TaskPriority.CRITICAL]
        high = [t for t in pending if t.priority == TaskPriority.HIGH]

        # Auto-promote eligible agents
        for agent in self.agents.values():
            if agent.can_promote_to_a:
                return json.dumps({
                    "action": "promote",
                    "agent_id": agent.agent_id,
                    "to_rank": "a_rank",
                    "reason": f"Uppfyller A-Rank-krav ({agent.tasks_completed} tasks, {agent.success_rate:.0%} success)",
                })
            if agent.can_promote_to_b:
                return json.dumps({
                    "action": "promote",
                    "agent_id": agent.agent_id,
                    "to_rank": "b_rank",
                    "reason": f"Uppfyller B-Rank-krav ({agent.tasks_completed} tasks, {agent.success_rate:.0%} success)",
                })

        # Spawn first agent if none exist
        if len(self.agents) == 0:
            task_hint = ""
            if critical:
                task_hint = f" — {len(critical)} kritiska tasks väntar"
            elif high:
                task_hint = f" — {len(high)} högprioriterade tasks väntar"
            return json.dumps({
                "action": "spawn",
                "name": "initial-python-agent",
                "language": "python",
                "reason": f"Seed agent — inga agenter i registret. {len(pending)} tasks i kö{task_hint}",
            })

        # Check if we have pending tasks but no capable agents
        capable = [a for a in self.agents.values()
                   if a.rank != AgentRank.LEVEL_0 and a.status == AgentStatus.IDLE]
        if pending and not capable:
            # Need to train agents so they can take tasks
            idle_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
            if idle_agents:
                agent = idle_agents[0]
                return json.dumps({
                    "action": "train",
                    "agent_id": agent.agent_id,
                    "focus": "code-review",
                    "reason": f"{agent.agent_id} måste nå B-Rank för att kunna ta tasks "
                              f"({len(pending)} väntar, varav {len(critical)} kritiska)",
                })

        # Idle training
        idle_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
        if idle_agents and self.loop_count % 3 == 0:
            agent = idle_agents[0]
            return json.dumps({
                "action": "train",
                "agent_id": agent.agent_id,
                "focus": "code-review",
                "reason": f"Active Idle — håller {agent.agent_id} skarp",
            })

        if pending:
            return json.dumps({
                "action": "noop",
                "reason": f"{len(pending)} tasks i kö men inga lediga B-Rank+ agenter. "
                          f"Avvaktar träning/befordran.",
            })

        return json.dumps({"action": "noop", "reason": "Systemet är stabilt — inga tasks, alla agenter redo"})

    # ─── Helpers ──────────────────────────────────────────────────────────

    def add_task(self, description: str, priority: str = "medium",
                 contract_type: str = "patch") -> str:
        """Add a task to the queue. Returns the task_id."""
        task = Task(
            task_id=f"task-{len(self.tasks)+1:04d}",
            description=description,
            priority=TaskPriority(priority),
            contract_type=contract_type,
        )
        self.tasks[task.task_id] = task
        self._save_state()
        return task.task_id

    def update_agent_from_result(self, task_id: str, success: bool,
                                  tests_passed: int = 0, tests_failed: int = 0) -> None:
        """Update agent stats from a task result."""
        task = self.tasks.get(task_id)
        if not task or not task.agent_id:
            return
        agent = self.agents.get(task.agent_id)
        if not agent:
            return

        agent.tasks_completed += 1
        agent.tests_passed += tests_passed
        agent.tests_failed += tests_failed

        total_tests = tests_passed + tests_failed
        if total_tests > 0:
            agent.success_rate = tests_passed / total_tests
        elif success:
            agent.success_rate = 1.0
        else:
            agent.success_rate = 0.0

        agent.status = AgentStatus.IDLE
        self._save_state()

    def _print_status(self) -> None:
        """Print a compact status line."""
        obs = self.observe()
        print(
            f"[status] agents={obs['agents_total']} "
            f"(idle={obs['agents_idle']} busy={obs['agents_busy']} err={obs['agents_error']}) "
            f"tasks_pending={obs['pending_tasks']} "
            f"VRAM free={obs['vram_free_gb']:.1f}GB "
            f"OOM={obs['oom_risk']['risk']}"
        )

    def _log(self, phase: str, message: str, level: str = "info") -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "level": level,
            "message": message,
        }
        self.event_log.append(entry)
        if level in ("warn", "error"):
            print(f"[{phase}/{level}] {message}")

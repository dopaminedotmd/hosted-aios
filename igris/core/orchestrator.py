"""
Commander Igris — Main Orchestrator.

Implements the core loop:
  Observe → Evaluate → Provision → Deploy

Features:
  - ANSI colors, GPU usage bar, live agent/task display
  - Interactive controls: s=status, t=tasks, a=agents, h=help, q=quit
  - Task-aware simulation mode

This is a SINGLETON — only one Igris instance runs per host.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from igris.core.contract_validator import (
    ContractType, ContractValidator, ContractEnvelope,
    AgentSpawnRequest, AgentSpawnResponse, TaskAssign, AgentPromote, AgentStatusUpdate,
)
from igris.core.gpu_manager import GPUManager
from igris.models.agent import Agent, AgentRank, AgentStatus
from igris.models.task import Task, TaskPriority, TaskStatus


# ─── ANSI Colors ──────────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# ─── Constants ────────────────────────────────────────────────────────────

DEFAULT_LOOP_INTERVAL_S = 5             # Default loop interval (seconds)
ACTIVE_IDLE_THRESHOLD_S = 15 * 60       # 15 minutes → Active Idle Mode


class IgrisOrchestrator:
    """Central orchestrator for Commander Igris multi-agent system.

    Start with enhanced chat display:
        igris = IgrisOrchestrator(data_dir=Path("data"))
        igris.chat()  # interactive mode

    Or plain loop:
        igris.run_loop()  # verbose terminal output
    """

    def __init__(self, data_dir: Path | str = Path("data")) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.validator = ContractValidator()
        self.gpu = GPUManager()

        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self.event_log: list[dict[str, Any]] = []

        self.last_human_input: Optional[datetime] = None
        self.active_idle: bool = False
        self.loop_count: int = 0

        self._load_state()

    # ─── State Persistence ─────────────────────────────────────────────────

    def _load_state(self) -> None:
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
        agents_data = [a.model_dump(mode="json") for a in self.agents.values()]
        tasks_data = [t.model_dump(mode="json") for t in self.tasks.values()]
        (self.data_dir / "agents.json").write_text(json.dumps(agents_data, indent=2, default=str))
        (self.data_dir / "tasks.json").write_text(json.dumps(tasks_data, indent=2, default=str))

    # ─── Observe Phase ────────────────────────────────────────────────────

    def observe(self) -> dict[str, Any]:
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
        try:
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
        name = decision.get("name", f"agent-{len(self.agents)+1:03d}")
        language = decision.get("language", "python")
        if not self.gpu.can_allocate(f"agent-{name}", 0.5):
            self._log("provision", f"VRAM budget exceeded, cannot spawn {name}", "warn")
            return None
        try:
            return self.validator.build_envelope(
                contract_type=ContractType.AGENT_SPAWN_REQUEST,
                sender_id="igris-core",
                payload={"name": name, "language": language,
                         "tools": ["read_file", "write_file", "terminal", "search_files"]},
            )
        except Exception as e:
            self._log("provision", f"Spawn contract build failed: {e}", "error")
            return None

    def _provision_assign(self, decision: dict) -> Optional[ContractEnvelope]:
        task_id = decision.get("task_id", "")
        agent_id = decision.get("agent_id", "")
        if task_id not in self.tasks:
            return None
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        if agent.status in (AgentStatus.BUSY, AgentStatus.ERROR):
            return None
        if agent.rank == AgentRank.LEVEL_0:
            return None
        try:
            return self.validator.build_envelope(
                contract_type=ContractType.TASK_ASSIGN,
                sender_id="igris-core", receiver_id=agent_id,
                payload={"task_id": task_id, "agent_id": agent_id,
                         "description": decision.get("description", ""),
                         "priority": decision.get("priority", "medium")},
            )
        except Exception as e:
            self._log("provision", f"Assign contract build failed: {e}", "error")
            return None

    def _provision_promote(self, decision: dict) -> Optional[ContractEnvelope]:
        agent_id = decision.get("agent_id", "")
        to_rank = decision.get("to_rank", "")
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        if to_rank == "b_rank" and not agent.can_promote_to_b:
            return None
        if to_rank == "a_rank" and not agent.can_promote_to_a:
            return None
        try:
            return self.validator.build_envelope(
                contract_type=ContractType.AGENT_PROMOTE,
                sender_id="igris-core", receiver_id=agent_id,
                payload={"agent_id": agent_id, "from_rank": agent.rank.value,
                         "to_rank": to_rank, "reason": decision.get("reason", "")},
            )
        except Exception as e:
            self._log("provision", f"Promote contract build failed: {e}", "error")
            return None

    def _provision_train(self, decision: dict) -> Optional[ContractEnvelope]:
        agent_id = decision.get("agent_id", "")
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        if agent.status != AgentStatus.IDLE:
            return None
        agent.status = AgentStatus.TRAINING
        agent._training_loop = self.loop_count
        focus = decision.get("focus", "general")
        self._log("provision", f"Agent {agent_id} → TRAINING (focus: {focus})")
        return None

    # ─── Deploy Phase ─────────────────────────────────────────────────────

    def deploy(self, envelope: ContractEnvelope) -> bool:
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
        payload = envelope.payload
        agent_id = f"agent-{payload['language']}-{len(self.agents)+1:03d}"
        agent = Agent(agent_id=agent_id, name=payload["name"],
                      language=payload["language"], rank=AgentRank.LEVEL_0,
                      status=AgentStatus.IDLE)
        self.agents[agent_id] = agent
        self.gpu.allocate(agent_id, 0.5)
        self._log("deploy", f"Spawned {agent_id} ({payload['language']}) — Level 0")
        self._save_state()
        return True

    def _deploy_assign(self, envelope: ContractEnvelope) -> bool:
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

    # ─── Main Loop (verbose) ──────────────────────────────────────────────

    def run_loop(self, router_fn=None, interval_s: int = DEFAULT_LOOP_INTERVAL_S,
                 verbose: bool = True) -> None:
        """Plain verbose loop. For enhanced mode, use chat()."""
        self._log("orchestrator", "Igris loop started")
        sep = "═" * 60
        thin = "─" * 60
        print(f"\n{sep}")
        print("  COMMANDER IGRIS — Realtidsövervakning")
        print(f"{sep}")
        print(f"  Loop: {interval_s}s  |  Agenter: {len(self.agents)}  |  Tasks: {len(self.tasks)}")
        print(f"{sep}\n")
        try:
            while True:
                self.loop_count += 1
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
                if router_fn:
                    router_output = router_fn(
                        [{"agent_id": a.agent_id, "rank": a.rank.value, "status": a.status.value,
                          "tasks_completed": a.tasks_completed, "success_rate": a.success_rate,
                          "language": a.language} for a in self.agents.values()],
                        [{"task_id": t.task_id, "priority": t.priority.value,
                          "status": t.status.value, "description": t.description}
                         for t in self.tasks.values() if t.status == TaskStatus.PENDING],
                        {"free_gb": obs["vram_free_gb"], "total_gb": self.gpu.hardware.gpu_vram_gb},
                        obs["oom_risk"],
                    )
                else:
                    router_output = self._simulate_router()
                decision = self.evaluate(router_output)
                if verbose:
                    action = decision.get("action", "?")
                    reason = decision.get("reason", "")
                    labels = {"spawn": "SPAWNA", "assign": "TILLDELA", "promote": "BEFORDRA",
                              "train": "TRÄNA", "noop": "INGEN ÅTGÄRD"}
                    print(f"  │")
                    print(f"  ├─ TÄNKER: {labels.get(action, action.upper())}")
                    if reason:
                        print(f"  │  └─ {reason}")
                    if action == "spawn":
                        print(f"  │     Namn: {decision.get('name', '?')} ({decision.get('language', '?')})")
                envelope = self.provision(decision)
                if envelope:
                    success = self.deploy(envelope)
                    icon = "✓" if success else "✗"
                    if verbose:
                        print(f"  │")
                        print(f"  └─ UTFÖR: {decision['action']} → {icon}")
                elif verbose and decision.get("action") != "noop":
                    print(f"  └─ BLOCKERAD: kunde inte provisioneras")
                if verbose:
                    print(f"{thin}\n")
                time.sleep(interval_s)
        except KeyboardInterrupt:
            self._log("orchestrator", "Loop interrupted")
            self._save_state()
            print(f"\n{sep}\n  Igris avslutad. State sparat.\n{sep}\n")

    # ─── Enhanced Chat Mode ───────────────────────────────────────────────

    @staticmethod
    def _check_key() -> str | None:
        """Non-blocking keypress check (Windows)."""
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getch().decode("utf-8", errors="ignore").lower()
        except ImportError:
            pass
        return None

    def _print_chat_banner(self, interval_s: int) -> None:
        print(f"\n{C.BOLD}{C.CYAN}╔{'═'*58}╗{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}║{C.RESET}  {C.BOLD}COMMANDER IGRIS — Direct Chat{C.RESET}" + " " * 25 + f"{C.BOLD}{C.CYAN}║{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}╠{'═'*58}╣{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}║{C.RESET}  {C.GRAY}Loop:{C.RESET} {interval_s}s    {C.GRAY}Idle:{C.RESET} 15min    "
              f"{C.GRAY}Agenter:{C.RESET} {len(self.agents):>3}    {C.GRAY}Tasks:{C.RESET} {len(self.tasks):>3}  {C.BOLD}{C.CYAN}║{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}╠{'═'*58}╣{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}║{C.RESET}  {C.GRAY}[s]tatus  [t]asks  [a]genter  [h]jälp  [q]uit{C.RESET}      {C.BOLD}{C.CYAN}║{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}╚{'═'*58}╝{C.RESET}")

    def _print_chat_observe(self) -> None:
        obs = self.observe()
        snap = self.gpu.snapshot()
        pct = snap.used_gb / snap.total_gb
        bar_w = 20
        filled = int(pct * bar_w)
        bar_color = C.GREEN if pct < 0.8 else C.YELLOW if pct < 0.95 else C.RED
        bar = bar_color + "█" * filled + C.GRAY + "░" * (bar_w - filled) + C.RESET
        oom = obs["oom_risk"]
        oom_colors = {"critical": C.RED + C.BOLD, "high": C.YELLOW, "moderate": C.CYAN, "low": C.GREEN}
        oom_str = oom_colors.get(oom["risk"], C.RESET) + oom["risk"].upper() + C.RESET
        print(f"\n{C.BOLD}#{self.loop_count:04d}{C.RESET}  {C.GRAY}OBSERVE{C.RESET}")
        print(f"    GPU [{bar}] {snap.used_gb:.1f}/{snap.total_gb:.1f} GB  "
              f"{snap.temperature_c}°C  OOM: {oom_str}")
        print(f"    Agenter: {obs['agents_total']} "
              f"({C.GREEN}{obs['agents_idle']} idle{C.RESET} "
              f"{C.CYAN}{obs['agents_busy']} busy{C.RESET} "
              f"{C.RED}{obs['agents_error']} err{C.RESET})  "
              f"Tasks: {C.YELLOW}{obs['pending_tasks']} pending{C.RESET}")

    def _print_chat_decision(self) -> dict:
        router_output = self._simulate_router()
        decision = self.evaluate(router_output)
        action = decision.get("action", "?")
        reason = decision.get("reason", "")
        labels = {"spawn": "SPAWNA", "assign": "TILLDELA", "promote": "BEFORDRA",
                  "train": "TRÄNA", "noop": "NOOP"}
        colors = {"spawn": C.GREEN, "assign": C.CYAN, "promote": C.MAGENTA,
                  "train": C.YELLOW, "noop": C.GRAY}
        print(f"    {C.BOLD}TÄNKER:{C.RESET} {colors.get(action, C.RESET)}{labels.get(action, action.upper())}{C.RESET}"
              f"  {C.DIM}{reason}{C.RESET}")
        if action == "spawn":
            print(f"          → {decision.get('name', '?')} ({decision.get('language', '?')})")
        elif action == "promote":
            print(f"          → {decision.get('agent_id', '?')} → {decision.get('to_rank', '?')}")
        elif action == "train":
            print(f"          → {decision.get('agent_id', '?')} | fokus: {decision.get('focus', '?')}")
        return decision

    def _print_chat_result(self, decision: dict) -> None:
        action = decision.get("action", "")
        if action == "train":
            print(f"    {C.BOLD}UTFÖR:{C.RESET} {C.YELLOW}→ TRÄNING{C.RESET}")
            return
        envelope = self.provision(decision)
        if envelope:
            success = self.deploy(envelope)
            icon = f"{C.GREEN}✓ OK{C.RESET}" if success else f"{C.RED}✗ FAIL{C.RESET}"
            print(f"    {C.BOLD}UTFÖR:{C.RESET} {icon}")
        elif action != "noop":
            print(f"    {C.RED}BLOCKERAD — kunde inte provisioneras{C.RESET}")

    def _print_chat_full_status(self) -> None:
        obs = self.observe()
        snap = self.gpu.snapshot()
        print(f"\n{C.BOLD}{'═'*58}{C.RESET}")
        print(f"{C.BOLD}  SYSTEMSTATUS{C.RESET}")
        print(f"{'─'*58}")
        print(f"  GPU: {snap.used_gb:.1f}/{snap.total_gb:.1f} GB | {snap.temperature_c}°C | "
              f"OOM: {obs['oom_risk']['risk'].upper()}")
        print(f"  Agenter: {obs['agents_total']} | Tasks: {obs['pending_tasks']} pending")
        print(f"\n{C.BOLD}  AGENTER:{C.RESET}")
        for agent in self.agents.values():
            icons = {"level_0": "⬜", "b_rank": "🟦", "a_rank": "🟪"}
            sc = {"idle": C.GRAY, "busy": C.CYAN, "training": C.YELLOW, "error": C.RED}
            print(f"  {icons.get(agent.rank.value, '⬜')} {agent.agent_id} | "
                  f"{agent.rank.value} | {sc.get(agent.status.value, C.RESET)}{agent.status.value}{C.RESET} | "
                  f"tasks: {agent.tasks_completed} | {agent.success_rate:.0%}")
        print(f"{'─'*58}")

    def _print_chat_tasks(self) -> None:
        print(f"\n{C.BOLD}{'═'*58}{C.RESET}")
        print(f"{C.BOLD}  TASK-KÖ{C.RESET}  ({len(self.tasks)} totalt)")
        print(f"{'─'*58}")
        for task in self.tasks.values():
            pc = {"critical": C.RED + C.BOLD, "high": C.YELLOW, "medium": C.CYAN, "low": C.GRAY}
            marker = "✓" if task.status.value == "completed" else "○" if task.status.value == "pending" else "●"
            print(f"  {marker} [{pc.get(task.priority.value, C.RESET)}{task.priority.value:8s}{C.RESET}] "
                  f"{task.task_id}: {task.description[:55]}")
        print(f"{'─'*58}")

    def _print_chat_help(self) -> None:
        print(f"""
{C.BOLD}KOMMANDON:{C.RESET}
  {C.CYAN}s{C.RESET} — Systemstatus (GPU, agenter, OOM)
  {C.CYAN}t{C.RESET} — Task-kö (alla tasks med prioritet)
  {C.CYAN}a{C.RESET} — Agentdetaljer
  {C.CYAN}h{C.RESET} — Denna hjälp
  {C.CYAN}q{C.RESET} — Avsluta Igris
""")

    def chat(self, interval_s: int = DEFAULT_LOOP_INTERVAL_S) -> None:
        """Enhanced interactive chat — the main Igris experience.

        Press keys during the loop: s=status, t=tasks, a=agents, h=help, q=quit.
        """
        self._log("orchestrator", "Igris chat started")
        self._print_chat_banner(interval_s)
        print(f"  {C.GREEN}Igris är redo. Tryck 'h' för hjälp.{C.RESET}")

        try:
            while True:
                # Auto-revert TRAINING agents after 3 loops
                for agent in self.agents.values():
                    if agent.status == AgentStatus.TRAINING:
                        if hasattr(agent, '_training_loop') and self.loop_count - agent._training_loop >= 3:
                            agent.status = AgentStatus.IDLE
                            agent.tasks_completed += 1
                            agent.success_rate = min(1.0, agent.success_rate + 0.05)
                            self._log("chat", f"{agent.agent_id} training complete → IDLE")

                self.loop_count += 1
                self._print_chat_observe()
                decision = self._print_chat_decision()
                self._print_chat_result(decision)

                # Interactive wait
                waited = 0.0
                while waited < interval_s:
                    key = self._check_key()
                    if key == "q":
                        print(f"\n{C.YELLOW}Avslutar Igris...{C.RESET}")
                        self._save_state()
                        return
                    elif key == "s":
                        self._print_chat_full_status()
                    elif key == "t":
                        self._print_chat_tasks()
                    elif key == "a":
                        self._print_chat_full_status()
                    elif key == "h":
                        self._print_chat_help()
                    time.sleep(0.1)
                    waited += 0.1

        except KeyboardInterrupt:
            self._save_state()
            print(f"\n{C.YELLOW}Igris avslutad. State sparat.{C.RESET}")

    # ─── Simulation Router ────────────────────────────────────────────────

    def _simulate_router(self) -> str:
        """Simulate router decisions with task awareness."""
        pending = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        critical = [t for t in pending if t.priority == TaskPriority.CRITICAL]
        high = [t for t in pending if t.priority == TaskPriority.HIGH]

        for agent in self.agents.values():
            if agent.can_promote_to_a:
                return json.dumps({"action": "promote", "agent_id": agent.agent_id,
                                   "to_rank": "a_rank",
                                   "reason": f"Uppfyller A-Rank ({agent.tasks_completed} tasks, {agent.success_rate:.0%})"})
            if agent.can_promote_to_b:
                return json.dumps({"action": "promote", "agent_id": agent.agent_id,
                                   "to_rank": "b_rank",
                                   "reason": f"Uppfyller B-Rank ({agent.tasks_completed} tasks, {agent.success_rate:.0%})"})

        if len(self.agents) == 0:
            hint = ""
            if critical:
                hint = f" — {len(critical)} kritiska tasks väntar"
            elif high:
                hint = f" — {len(high)} högprioriterade tasks väntar"
            return json.dumps({"action": "spawn", "name": "initial-python-agent",
                               "language": "python",
                               "reason": f"Seed agent — inga agenter. {len(pending)} tasks i kö{hint}"})

        capable = [a for a in self.agents.values()
                   if a.rank != AgentRank.LEVEL_0 and a.status == AgentStatus.IDLE]
        if pending and not capable:
            idle_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
            if idle_agents:
                agent = idle_agents[0]
                return json.dumps({"action": "train", "agent_id": agent.agent_id,
                                   "focus": "code-review",
                                   "reason": f"{agent.agent_id} måste nå B-Rank ({len(pending)} tasks väntar, {len(critical)} kritiska)"})

        idle_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
        if idle_agents and self.loop_count % 3 == 0:
            agent = idle_agents[0]
            return json.dumps({"action": "train", "agent_id": agent.agent_id,
                               "focus": "code-review",
                               "reason": f"Active Idle — håller {agent.agent_id} skarp"})

        if pending:
            return json.dumps({"action": "noop",
                               "reason": f"{len(pending)} tasks i kö men inga lediga B-Rank+ agenter"})

        return json.dumps({"action": "noop", "reason": "Systemet är stabilt — inga tasks, alla agenter redo"})

    # ─── Public API ───────────────────────────────────────────────────────

    def add_task(self, description: str, priority: str = "medium",
                 contract_type: str = "patch") -> str:
        task = Task(task_id=f"task-{len(self.tasks)+1:04d}", description=description,
                    priority=TaskPriority(priority), contract_type=contract_type)
        self.tasks[task.task_id] = task
        self._save_state()
        return task.task_id

    def update_agent_from_result(self, task_id: str, success: bool,
                                  tests_passed: int = 0, tests_failed: int = 0) -> None:
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
        obs = self.observe()
        print(f"[status] agents={obs['agents_total']} "
              f"(idle={obs['agents_idle']} busy={obs['agents_busy']} err={obs['agents_error']}) "
              f"tasks_pending={obs['pending_tasks']} "
              f"VRAM free={obs['vram_free_gb']:.1f}GB "
              f"OOM={obs['oom_risk']['risk']}")

    def _log(self, phase: str, message: str, level: str = "info") -> None:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "phase": phase, "level": level, "message": message}
        self.event_log.append(entry)
        if level in ("warn", "error"):
            print(f"[{phase}/{level}] {message}")

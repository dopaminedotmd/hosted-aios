"""
Commander Igris — Direct Chat / Realtidsövervakning.

Enhanced terminal UI with:
  - ANSI colors (green=success, red=error, yellow=GPU, cyan=info)
  - Interactive controls: s=status, t=tasks, a=agents, q=quit
  - Live agent state display
  - Task queue preview
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Ensure the igris package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from igris.core.orchestrator import IgrisOrchestrator
from igris.models.task import TaskStatus, TaskPriority
from igris.models.agent import AgentStatus


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
    BG_DARK = "\033[48;5;234m"


# ─── Helpers ──────────────────────────────────────────────────────────────

def _agent_icon(rank: str) -> str:
    icons = {"level_0": "⬜", "b_rank": "🟦", "a_rank": "🟪", "s_rank": "🟨"}
    return icons.get(rank, "⬜")


def _status_color(status: str) -> str:
    colors = {"idle": C.GRAY, "busy": C.CYAN, "training": C.YELLOW, "error": C.RED}
    return colors.get(status, C.RESET)


def _priority_color(priority: str) -> str:
    colors = {"critical": C.RED + C.BOLD, "high": C.YELLOW, "medium": C.CYAN, "low": C.GRAY}
    return colors.get(priority, C.RESET)


def _oom_color(risk: str) -> str:
    colors = {"critical": C.RED + C.BOLD, "high": C.YELLOW, "moderate": C.CYAN, "low": C.GREEN}
    return colors.get(risk, C.RESET)


def _check_key() -> str | None:
    """Non-blocking keypress check (Windows only)."""
    try:
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
            return key
    except ImportError:
        pass
    return None


def _print_banner(igris: IgrisOrchestrator, interval_s: int) -> None:
    s = C.BOLD + C.CYAN
    r = C.RESET
    print(f"\n{s}╔{'═'*58}╗{r}")
    print(f"{s}║{r}  {C.BOLD}COMMANDER IGRIS — Direct Chat{C.RESET}" + " " * 25 + f"{s}║{r}")
    print(f"{s}╠{'═'*58}╣{r}")
    print(f"{s}║{r}  {C.GRAY}Loop:{C.RESET} {interval_s}s    {C.GRAY}Active Idle:{C.RESET} 15 min    {C.GRAY}Agenter:{C.RESET} {len(igris.agents):>3}    {C.GRAY}Tasks:{C.RESET} {len(igris.tasks):>3}  {s}║{r}")
    print(f"{s}╠{'═'*58}╣{r}")
    print(f"{s}║{r}  {C.GRAY}[s]tatus  [t]asks  [a]genter  [h]jälp  [q]uit{C.RESET}      {s}║{r}")
    print(f"{s}╚{'═'*58}╝{r}\n")


def _print_observe(igris: IgrisOrchestrator, loop: int) -> None:
    obs = igris.observe()
    snap = igris.gpu.snapshot()

    # GPU bar
    pct = snap.used_gb / snap.total_gb
    bar_w = 20
    filled = int(pct * bar_w)
    bar_color = C.GREEN if pct < 0.8 else C.YELLOW if pct < 0.95 else C.RED
    bar = bar_color + "█" * filled + C.GRAY + "░" * (bar_w - filled) + C.RESET

    oom = obs["oom_risk"]
    oom_str = _oom_color(oom["risk"]) + oom["risk"].upper() + C.RESET

    print(f"{C.BOLD}#{loop:04d}{C.RESET}  {C.GRAY}OBSERVE{C.RESET}")
    print(f"    GPU [{bar}] {snap.used_gb:.1f}/{snap.total_gb:.1f} GB  {snap.temperature_c}°C  OOM: {oom_str}")
    print(f"    Agenter: {obs['agents_total']} ({C.GREEN}{obs['agents_idle']} idle{C.RESET} {C.CYAN}{obs['agents_busy']} busy{C.RESET} {C.RED}{obs['agents_error']} err{C.RESET})  "
          f"Tasks: {C.YELLOW}{obs['pending_tasks']} pending{C.RESET}")


def _print_decision(igris: IgrisOrchestrator) -> dict:
    router_output = igris._simulate_router()
    decision = igris.evaluate(router_output)
    action = decision.get("action", "?")
    reason = decision.get("reason", "")

    labels = {"spawn": "SPAWNA", "assign": "TILLDELA", "promote": "BEFORDRA",
              "train": "TRÄNA", "noop": "NOOP"}
    colors = {"spawn": C.GREEN, "assign": C.CYAN, "promote": C.MAGENTA,
              "train": C.YELLOW, "noop": C.GRAY}
    label = labels.get(action, action.upper())
    color = colors.get(action, C.RESET)

    print(f"    {C.BOLD}TANKER:{C.RESET} {color}{label}{C.RESET}  {C.DIM}{reason}{C.RESET}")

    if action == "spawn":
        print(f"          → {decision.get('name', '?')} ({decision.get('language', '?')})")
    elif action == "promote":
        print(f"          → {decision.get('agent_id', '?')} → {decision.get('to_rank', '?')}")
    elif action == "train":
        print(f"          → {decision.get('agent_id', '?')} | fokus: {decision.get('focus', '?')}")

    return decision


def _print_result(igris: IgrisOrchestrator, decision: dict) -> None:
    envelope = igris.provision(decision)
    if envelope:
        success = igris.deploy(envelope)
        icon = f"{C.GREEN}OK{C.RESET}" if success else f"{C.RED}FAIL{C.RESET}"
        print(f"    {C.BOLD}UTFOR:{C.RESET} {icon}")
    elif decision.get("action") != "noop":
        print(f"    {C.RED}BLOCKERAD — kunde inte provisioneras{C.RESET}")


def _print_status(igris: IgrisOrchestrator) -> None:
    print(f"\n{C.BOLD}{'═'*58}{C.RESET}")
    print(f"{C.BOLD}  SYSTEMSTATUS{C.RESET}")
    print(f"{'─'*58}")
    igris._print_status()
    print(f"\n{C.BOLD}  AGENTER:{C.RESET}")
    for agent in igris.agents.values():
        icon = _agent_icon(agent.rank.value)
        sc = _status_color(agent.status.value)
        print(f"  {icon} {agent.agent_id} | {agent.rank.value} | {sc}{agent.status.value}{C.RESET} | "
              f"tasks: {agent.tasks_completed} | success: {agent.success_rate:.0%}")
    print(f"{'─'*58}\n")


def _print_tasks(igris: IgrisOrchestrator) -> None:
    print(f"\n{C.BOLD}{'═'*58}{C.RESET}")
    print(f"{C.BOLD}  TASK-KÖ{C.RESET}  ({len(igris.tasks)} totalt)")
    print(f"{'─'*58}")
    for task in igris.tasks.values():
        pc = _priority_color(task.priority.value)
        status = task.status.value
        marker = "✓" if status == "completed" else "○" if status == "pending" else "●"
        print(f"  {marker} [{pc}{task.priority.value:8s}{C.RESET}] {task.task_id}: {task.description[:60]}")
    print(f"{'─'*58}\n")


def _print_help() -> None:
    print(f"""
{C.BOLD}KOMMANDON:{C.RESET}
  {C.CYAN}s{C.RESET} — Systemstatus (agenter, GPU, OOM)
  {C.CYAN}t{C.RESET} — Task-kö (alla tasks med prioritet)
  {C.CYAN}a{C.RESET} — Agentdetaljer (rank, status, historik)
  {C.CYAN}h{C.RESET} — Denna hjälp
  {C.CYAN}q{C.RESET} — Avsluta Igris
""")


# ─── Main Chat Loop ───────────────────────────────────────────────────────

def run_chat(data_dir: str = "data", interval_s: int = 5) -> None:
    """Start Igris with enhanced interactive terminal UI.

    Press keys during the loop to interact:
      s = full status   t = task list   a = agent list
      h = help          q = quit
    """
    igris = IgrisOrchestrator(data_dir=Path(data_dir))

    _print_banner(igris, interval_s)
    print(f"  {C.GREEN}Igris är redo. Tryck 'h' för hjälp.{C.RESET}\n")

    try:
        while True:
            igris.loop_count += 1

            # ── OBSERVE ──
            _print_observe(igris, igris.loop_count)

            # ── THINK ──
            decision = _print_decision(igris)

            # ── EXECUTE ──
            _print_result(igris, decision)

            # ── WAIT with interactive input ──
            print()  # blank line between loops
            waited = 0
            while waited < interval_s:
                key = _check_key()
                if key == "q":
                    print(f"\n{C.YELLOW}Avslutar Igris...{C.RESET}")
                    igris._save_state()
                    return
                elif key == "s":
                    _print_status(igris)
                elif key == "t":
                    _print_tasks(igris)
                elif key == "a":
                    _print_status(igris)  # shows agents
                elif key == "h":
                    _print_help()
                time.sleep(0.1)
                waited += 0.1

    except KeyboardInterrupt:
        igris._save_state()
        print(f"\n{C.YELLOW}Igris avslutad. State sparat.{C.RESET}")


# ─── CLI Entry ────────────────────────────────────────────────────────────

def main() -> None:
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run_chat(data_dir=data_dir, interval_s=interval)


if __name__ == "__main__":
    main()

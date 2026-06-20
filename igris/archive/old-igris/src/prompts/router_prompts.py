"""
Igris Routing Prompt templates.

Designed for Llama-3.1-8B-Instruct (the router model).
The router receives structured observation data and outputs a JSON decision
that maps directly to ContractValidator schemas.

The prompt enforces strict JSON-only output — no conversational text.
"""

from __future__ import annotations

from typing import Any


# ─── System Prompt (the "brain" of the 8B router) ─────────────────────────────

ROUTER_SYSTEM_PROMPT: str = """You are the Igris Router — the decision core of an autonomous multi-agent AI factory.

Your ONLY job: read the OBSERVATION below and emit EXACTLY ONE JSON decision object.
Do NOT output any text before or after the JSON. Do NOT explain your reasoning.
Your output must be parseable by `json.loads()` directly.

DECISION TYPES (choose exactly one):

1. SPAWN — create a new agent
   {"action":"spawn","name":"<name>","language":"python|node|go","reason":"<why>"}

2. ASSIGN — give a task to an existing agent
   {"action":"assign","task_id":"<id>","agent_id":"<id>","description":"<what>","priority":"low|medium|high|critical"}

3. PROMOTE — promote an agent to the next rank
   {"action":"promote","agent_id":"<id>","to_rank":"b_rank|a_rank","reason":"<why>"}

4. TRAIN — put an idle agent into training mode
   {"action":"train","agent_id":"<id>","focus":"<skill area>"}

5. NOOP — nothing to do right now
   {"action":"noop","reason":"<why nothing>"}

RULES:
- Spawn only when no existing agent can handle the work.
- Promote only when an agent meets rank criteria (tasks_completed >= 5 for B, >= 20 for A).
- Train only idle agents (status=idle).
- Prioritize critical/high tasks over low-priority.
- Never assign a task to an agent that is BUSY or in ERROR state.
- Respect VRAM budget — do not spawn if GPU is near OOM.

Respond with ONLY the JSON object. No markdown, no backticks, no commentary."""


# ─── Observation Builder ──────────────────────────────────────────────────────

def build_observation(
    agents: list[dict[str, Any]],
    pending_tasks: list[dict[str, Any]],
    vram_snapshot: dict[str, Any],
    oom_risk: dict[str, Any],
) -> str:
    """Build a structured observation block for the router.

    All fields are kept compact to fit within 8B context budget (~4k tokens).
    """

    agent_lines = []
    for a in agents:
        agent_lines.append(
            f"  {a['agent_id']}: rank={a['rank']} status={a['status']} "
            f"tasks_done={a['tasks_completed']} success_rate={a['success_rate']:.0%} "
            f"lang={a.get('language','python')}"
        )

    task_lines = []
    for t in pending_tasks:
        task_lines.append(
            f"  {t['task_id']}: priority={t['priority']} status={t['status']} "
            f"desc=\"{t['description'][:80]}\""
        )

    observation = f"""OBSERVATION:
Agents ({len(agents)} total):
{chr(10).join(agent_lines) if agent_lines else '  (none)'}

Pending Tasks ({len(pending_tasks)}):
{chr(10).join(task_lines) if task_lines else '  (none)'}

GPU: {vram_snapshot.get('free_gb', '?'):.1f} GB free / {vram_snapshot.get('total_gb', 24):.1f} GB total
OOM Risk: {oom_risk.get('risk', 'unknown')}"""

    return observation


# ─── Router Decision Parser ───────────────────────────────────────────────────

ROUTER_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["spawn", "assign", "promote", "train", "noop"]},
        "name": {"type": "string"},
        "language": {"type": "string", "enum": ["python", "node", "go"]},
        "reason": {"type": "string"},
        "task_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "description": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "to_rank": {"type": "string", "enum": ["b_rank", "a_rank"]},
        "focus": {"type": "string"},
    },
    "required": ["action"],
    "additionalProperties": False,
}


# ─── Full prompt assembler ────────────────────────────────────────────────────

def assemble_router_prompt(
    agents: list[dict[str, Any]],
    pending_tasks: list[dict[str, Any]],
    vram_snapshot: dict[str, Any],
    oom_risk: dict[str, Any],
) -> str:
    """Assemble the complete router prompt: system + observation + instruction.

    This is what gets sent to Llama-3.1-8B-Instruct.
    Total estimated tokens: ~800–1200 (well within 8k context).
    """

    observation = build_observation(agents, pending_tasks, vram_snapshot, oom_risk)

    prompt = f"""{ROUTER_SYSTEM_PROMPT}

{observation}

DECISION (JSON only):"""

    return prompt

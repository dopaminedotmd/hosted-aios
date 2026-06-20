"""
Commander Igris — Desktop Application.

A native Windows desktop app (CustomTkinter) with:
  - Direct chat with qwen2.5-coder:32b via Ollama
  - Agent status panel
  - GPU/VRAM monitor
  - Command interface for spawning agents, scanning repos, etc.

Run: python -m igris.desktop
"""

from __future__ import annotations

import json
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import requests

# Ensure igris is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from igris.core.orchestrator import IgrisOrchestrator
from igris.core.gpu_manager import GPUManager

# ─── Theme ───────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Igris custom colors
class C:
    BG = "#0a0a0f"
    SIDEBAR = "#111118"
    ACCENT = "#6c5ce7"
    CHAT_USER = "#1a1a2e"
    CHAT_IGRIS = "#0f0f18"
    GREEN = "#00e676"
    YELLOW = "#ffd600"
    RED = "#ff1744"

OLLAMA_URL = "http://localhost:11434"
MAIN_MODEL = "qwen2.5-coder:32b"


class IgrisDesktop(ctk.CTk):
    """Main desktop application window."""

    def __init__(self):
        super().__init__()

        self.title("Commander Igris")
        self.geometry("1280x820")
        self.minsize(900, 600)
        self.configure(fg_color=C.BG)

        # State
        self.orchestrator = IgrisOrchestrator(data_dir=Path("igris/data"))
        self.gpu = GPUManager()
        self.chat_history: list[dict] = []
        self._response_queue: queue.Queue = queue.Queue()
        self._streaming = False

        # Build UI
        self._build_layout()
        self._load_initial_state()

        # Start GPU monitor
        self._monitor_gpu()

    # ─── Layout ───────────────────────────────────────────────────────────

    def _build_layout(self):
        # Main grid: sidebar | chat
        self.grid_columnconfigure(0, weight=3)  # chat
        self.grid_columnconfigure(1, weight=1)  # sidebar
        self.grid_rowconfigure(0, weight=1)

        self._build_chat_panel()
        self._build_sidebar()
        self._build_command_bar()

    def _build_chat_panel(self):
        """Left panel: chat history + input."""
        chat_frame = ctk.CTkFrame(self, fg_color=C.BG, corner_radius=0)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(1, weight=0)
        chat_frame.grid_columnconfigure(0, weight=1)

        # Chat header
        header = ctk.CTkFrame(chat_frame, fg_color=C.SIDEBAR, height=40, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 0))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="◈  COMMANDER IGRIS  —  Direct Link",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C.ACCENT,
        ).pack(side="left", padx=15, pady=8)

        self._model_label = ctk.CTkLabel(
            header, text=f"qwen2.5-coder:32b",
            font=ctk.CTkFont(size=11),
            text_color="#666",
        )
        self._model_label.pack(side="right", padx=15, pady=8)

        # Chat text area (read-only)
        self.chat_text = ctk.CTkTextbox(
            chat_frame,
            fg_color=C.BG,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=12),
            wrap="word",
            state="disabled",
            border_width=0,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=(45, 10))

        # Input frame
        input_frame = ctk.CTkFrame(chat_frame, fg_color=C.SIDEBAR, corner_radius=8)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.chat_input = ctk.CTkTextbox(
            input_frame,
            height=55,
            fg_color=C.SIDEBAR,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=12),
            wrap="word",
            border_width=0,
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.chat_input.bind("<Return>", self._on_send)
        self.chat_input.bind("<Shift-Return>", lambda e: None)  # allow newlines

        # Send button
        send_btn = ctk.CTkButton(
            input_frame,
            text="▶",
            width=40,
            height=35,
            fg_color=C.ACCENT,
            hover_color="#7c6cf0",
            command=self._send_message,
        )
        send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Quick commands row
        quick_frame = ctk.CTkFrame(chat_frame, fg_color=C.BG)
        quick_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))

        commands = [
            ("/status", self._cmd_status),
            ("/agents", self._cmd_agents),
            ("/gpu", self._cmd_gpu),
            ("/scan", self._cmd_scan),
            ("/spawn python", self._cmd_spawn_python),
            ("/clear", self._cmd_clear),
        ]
        for label, cmd in commands:
            btn = ctk.CTkButton(
                quick_frame, text=label, width=70, height=22,
                fg_color="#1a1a2e", hover_color=C.ACCENT,
                font=ctk.CTkFont(size=10), command=cmd,
            )
            btn.pack(side="left", padx=2)

    def _build_sidebar(self):
        """Right panel: agent status, GPU, repo-map."""
        sidebar = ctk.CTkFrame(self, fg_color=C.SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_rowconfigure(0, weight=1)
        sidebar.grid_rowconfigure(1, weight=0)

        # Tab view
        self.sidebar_tabs = ctk.CTkTabview(sidebar, fg_color=C.SIDEBAR)
        self.sidebar_tabs.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sidebar.grid_columnconfigure(0, weight=1)

        # Agents tab
        agents_tab = self.sidebar_tabs.add("Agenter")
        self.agents_text = ctk.CTkTextbox(
            agents_tab, fg_color=C.SIDEBAR, text_color="#e0e0e0",
            font=ctk.CTkFont(size=11), wrap="word", state="disabled",
            border_width=0,
        )
        self.agents_text.pack(fill="both", expand=True, padx=5, pady=5)

        # GPU tab
        gpu_tab = self.sidebar_tabs.add("GPU")
        self.gpu_text = ctk.CTkTextbox(
            gpu_tab, fg_color=C.SIDEBAR, text_color="#e0e0e0",
            font=ctk.CTkFont(size=11), wrap="word", state="disabled",
            border_width=0,
        )
        self.gpu_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Tasks tab
        tasks_tab = self.sidebar_tabs.add("Tasks")
        self.tasks_text = ctk.CTkTextbox(
            tasks_tab, fg_color=C.SIDEBAR, text_color="#e0e0e0",
            font=ctk.CTkFont(size=11), wrap="word", state="disabled",
            border_width=0,
        )
        self.tasks_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Status bar (bottom)
        self.status_bar = ctk.CTkLabel(
            sidebar, text="◈ IG RIS  READY",
            font=ctk.CTkFont(size=10),
            text_color="#555",
            height=25,
        )
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

    def _build_command_bar(self):
        """Bottom command bar for quick actions."""
        # Commands are integrated in the quick commands row above chat input
        pass

    # ─── Chat Logic ────────────────────────────────────────────────────────

    def _on_send(self, event=None):
        """Handle Enter key in input."""
        if event and event.state & 0x1:  # Shift held
            return
        self._send_message()
        return "break"  # prevent newline

    def _send_message(self):
        """Send message to qwen2.5-coder."""
        text = self.chat_input.get("1.0", "end-1c").strip()
        if not text or self._streaming:
            return

        # Handle commands
        if text.startswith("/"):
            self._handle_command(text)
            self.chat_input.delete("1.0", "end")
            return

        self.chat_input.delete("1.0", "end")
        self._append_chat("YOU", text, C.GREEN)
        self.chat_history.append({"role": "user", "content": text})

        # Stream response in background
        self._streaming = True
        self.status_bar.configure(text="◈ IG RIS  THINKING...", text_color=C.YELLOW)
        self._append_chat("IGRIS", "", C.ACCENT, is_stream=True)

        thread = threading.Thread(target=self._stream_ollama, args=(text,), daemon=True)
        thread.start()
        self._poll_stream()

    def _stream_ollama(self, user_message: str):
        """Stream response from Ollama in background thread."""
        try:
            payload = {
                "model": MAIN_MODEL,
                "messages": self.chat_history,
                "stream": True,
                "options": {"temperature": 0.7, "num_predict": 2048},
            }
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120
            )
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if chunk.get("done"):
                        full = "".join(chunk.get("message", {}).get("content", ""))
                        self._response_queue.put(("done", content))
                    else:
                        self._response_queue.put(("chunk", content))
        except Exception as e:
            self._response_queue.put(("error", str(e)))

    def _poll_stream(self):
        """Poll the response queue and update UI."""
        full_response = ""
        try:
            while True:
                kind, data = self._response_queue.get_nowait()
                if kind == "chunk":
                    full_response += data
                    self._update_stream(full_response)
                elif kind == "done":
                    full_response += data
                    self._update_stream(full_response)
                    self._finalize_response(full_response)
                    return
                elif kind == "error":
                    self._append_chat("ERROR", data, C.RED)
                    self._streaming = False
                    self.status_bar.configure(text="◈ IG RIS  READY", text_color="#555")
                    return
        except queue.Empty:
            pass

        if self._streaming:
            self.after(50, self._poll_stream)

    def _update_stream(self, text: str):
        """Update the streaming response in-place."""
        self.chat_text.configure(state="normal")
        # Remove last line (the streaming placeholder)
        last_line_start = self.chat_text.index("end-2l linestart")
        self.chat_text.delete(last_line_start, "end-1c")
        self._insert_colored("IGRIS", text, C.ACCENT)
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def _finalize_response(self, full_response: str):
        """Finalize the streaming response."""
        self.chat_history.append({"role": "assistant", "content": full_response})
        self._streaming = False
        self.status_bar.configure(text="◈ IG RIS  READY", text_color="#555")
        self._refresh_sidebar()

    def _append_chat(self, sender: str, text: str, color: str, is_stream: bool = False):
        """Append a message to the chat display."""
        self.chat_text.configure(state="normal")
        if self.chat_text.get("1.0", "end-1c").strip():
            self.chat_text.insert("end", "\n\n")
        self._insert_colored(sender, text, color)
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def _insert_colored(self, sender: str, text: str, color: str):
        """Insert colored sender + text."""
        self.chat_text.insert("end", f"{sender}: ", ("sender",))
        self.chat_text.insert("end", text)

        # Configure tag for sender color
        self.chat_text.tag_config("sender", foreground=color)

    # ─── Commands ──────────────────────────────────────────────────────────

    def _handle_command(self, text: str):
        cmd = text.lower().strip()
        if cmd.startswith("/status"):
            self._cmd_status()
        elif cmd.startswith("/agents"):
            self._cmd_agents()
        elif cmd.startswith("/gpu"):
            self._cmd_gpu()
        elif cmd.startswith("/scan"):
            self._cmd_scan()
        elif cmd.startswith("/spawn"):
            parts = cmd.split()
            lang = parts[1] if len(parts) > 1 else "python"
            self._cmd_spawn(lang)
        elif cmd.startswith("/clear"):
            self._cmd_clear()
        elif cmd.startswith("/help"):
            self._cmd_help()
        else:
            self._append_chat("IGRIS", f"Unknown command: {cmd}\nType /help for available commands.", C.RED)

    def _cmd_status(self):
        obs = self.orchestrator.observe()
        msg = (
            f"══ SYSTEM STATUS ══\n"
            f"Agents: {obs['agents_total']} total ({obs['agents_idle']} idle, {obs['agents_busy']} busy, {obs['agents_error']} errors)\n"
            f"Pending tasks: {obs['pending_tasks']}\n"
            f"GPU: {obs['vram_free_gb']:.1f} GB free / {obs['vram_used_gb']:.1f} GB used ({obs['gpu_util_pct']}% util)\n"
            f"OOM risk: {obs['oom_risk']['risk']}\n"
            f"Active Idle: {'ON' if obs['active_idle_mode'] else 'OFF'}\n"
            f"Loop count: {obs['loop_count']}"
        )
        self._append_chat("IGRIS", msg, C.ACCENT)
        self._refresh_sidebar()

    def _cmd_agents(self):
        agents = self.orchestrator.agents
        if not agents:
            self._append_chat("IGRIS", "No agents registered.", C.ACCENT)
            return
        lines = ["══ AGENTS ══"]
        for a in agents.values():
            rank_icon = {"level_0": "○", "b_rank": "◈", "a_rank": "◆"}.get(a.rank.value, "?")
            status_icon = {"idle": "💤", "training": "🏋", "busy": "⚡", "error": "💀"}.get(a.status.value, "?")
            lines.append(
                f"{rank_icon} {a.agent_id} | {a.rank.value} | {status_icon} {a.status.value} | "
                f"tasks: {a.tasks_completed} | SR: {a.success_rate:.0%}"
            )
        self._append_chat("IGRIS", "\n".join(lines), C.ACCENT)
        self._refresh_sidebar()

    def _cmd_gpu(self):
        snap = self.gpu.snapshot()
        risk = self.gpu.check_oom_risk()
        msg = (
            f"══ GPU STATUS ══\n"
            f"RTX 3090 24 GB\n"
            f"Used: {snap.used_gb:.1f} GB | Free: {snap.free_gb:.1f} GB\n"
            f"Utilization: {snap.utilization_pct}%\n"
            f"Temperature: {snap.temperature_c}°C\n"
            f"OOM Risk: {risk['risk']} → {risk['action']}"
        )
        self._append_chat("IGRIS", msg, C.ACCENT)

    def _cmd_scan(self):
        from igris.cartographer import RepoCartographer
        self._append_chat("IGRIS", "Scanning current project...", C.ACCENT)
        try:
            ctg = RepoCartographer("igris")
            m = ctg.scan_incremental()
            msg = (
                f"══ REPO SCAN ══\n"
                f"Root: {m.repo_root}\n"
                f"Files: {m.total_files} | Symbols: {m.total_symbols}\n"
                f"Languages: {dict(m.languages)}\n"
                f"Cache: .igris/cartographer_cache.json"
            )
            self._append_chat("IGRIS", msg, C.ACCENT)
        except Exception as e:
            self._append_chat("IGRIS", f"Scan failed: {e}", C.RED)

    def _cmd_spawn(self, language: str = "python"):
        task_id = self.orchestrator.add_task(
            f"Autonomous {language} agent task", priority="medium", contract_type="scaffold"
        )
        # Simulate spawn decision
        from igris.core.contract_validator import ContractType
        envelope = self.orchestrator.validator.build_envelope(
            contract_type=ContractType.AGENT_SPAWN_REQUEST,
            sender_id="igris-desktop",
            payload={"name": f"agent-{language}-{len(self.orchestrator.agents)+1:03d}", "language": language},
        )
        self.orchestrator.deploy(envelope)
        self._append_chat(
            "IGRIS",
            f"Spawned new Level-0 {language} agent.\nTask {task_id} created.",
            C.GREEN,
        )
        self._refresh_sidebar()

    def _cmd_spawn_python(self):
        self._cmd_spawn("python")

    def _cmd_clear(self):
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")

    def _cmd_help(self):
        msg = (
            "══ COMMANDS ══\n"
            "/status      System overview\n"
            "/agents      List all agents\n"
            "/gpu         GPU/VRAM status\n"
            "/scan        Scan current project\n"
            "/spawn <lang> Spawn a new agent (python/node/go)\n"
            "/clear       Clear chat\n"
            "/help        Show this help\n\n"
            "Any other text → direct chat with qwen2.5-coder:32b"
        )
        self._append_chat("IGRIS", msg, C.ACCENT)

    # ─── Sidebar Refresh ───────────────────────────────────────────────────

    def _refresh_sidebar(self):
        """Update agent/GPU/task panels."""
        # Agents
        self.agents_text.configure(state="normal")
        self.agents_text.delete("1.0", "end")
        agents = self.orchestrator.agents
        if agents:
            for a in agents.values():
                rank_icon = {"level_0": "[0]", "b_rank": "[B]", "a_rank": "[A]"}.get(a.rank.value, "[?]")
                self.agents_text.insert("end", f"{rank_icon} {a.agent_id}\n")
                self.agents_text.insert("end", f"  {a.status.value} | tasks:{a.tasks_completed} | SR:{a.success_rate:.0%}\n\n")
        else:
            self.agents_text.insert("end", "(no agents)\n\nSpawn one with /spawn python")
        self.agents_text.configure(state="disabled")

        # GPU
        self.gpu_text.configure(state="normal")
        self.gpu_text.delete("1.0", "end")
        try:
            snap = self.gpu.snapshot()
            risk = self.gpu.check_oom_risk()
            self.gpu_text.insert("end", f"RTX 3090 24 GB\n")
            self.gpu_text.insert("end", f"Used:  {snap.used_gb:.1f} GB\n")
            self.gpu_text.insert("end", f"Free:  {snap.free_gb:.1f} GB\n")
            self.gpu_text.insert("end", f"Util:  {snap.utilization_pct}%\n")
            self.gpu_text.insert("end", f"Temp:  {snap.temperature_c}°C\n\n")
            self.gpu_text.insert("end", f"OOM: {risk['risk']}\n")
            self.gpu_text.insert("end", f"→ {risk['action']}\n")
        except Exception as e:
            self.gpu_text.insert("end", f"GPU error: {e}")
        self.gpu_text.configure(state="disabled")

        # Tasks
        self.tasks_text.configure(state="normal")
        self.tasks_text.delete("1.0", "end")
        tasks = self.orchestrator.tasks
        if tasks:
            for t in tasks.values():
                prio_icon = {"critical": "!!", "high": "! ", "medium": "· ", "low": "  "}.get(t.priority.value, "  ")
                self.tasks_text.insert("end", f"{prio_icon} {t.task_id}\n")
                self.tasks_text.insert("end", f"  [{t.status.value}] {t.description[:50]}\n\n")
        else:
            self.tasks_text.insert("end", "(no tasks)")
        self.tasks_text.configure(state="disabled")

    # ─── GPU Monitor ───────────────────────────────────────────────────────

    def _monitor_gpu(self):
        """Periodically refresh GPU sidebar."""
        try:
            self._refresh_sidebar()
        except Exception:
            pass
        self.after(5000, self._monitor_gpu)  # every 5s

    # ─── Initial State ─────────────────────────────────────────────────────

    def _load_initial_state(self):
        """Load initial chat welcome message."""
        welcome = (
            "Commander Igris online.\n\n"
            "Direct link to qwen2.5-coder:32b established.\n"
            "Type anything to chat with the model, or use /commands:\n\n"
            "  /status   — System overview\n"
            "  /agents   — Agent registry\n"
            "  /gpu      — GPU/VRAM status\n"
            "  /scan     — Scan project\n"
            "  /spawn    — Spawn agent\n"
            "  /help     — All commands"
        )
        self._append_chat("IGRIS", welcome, C.ACCENT)
        self._refresh_sidebar()


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    app = IgrisDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()

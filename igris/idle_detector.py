"""
Idle Detector for Commander Igris.

Monitors time since last human input and triggers Active Idle Mode
when no input has been received for >15 minutes.

Active Idle Mode behaviour:
  - Igris takes 90% of GPU compute
  - Prioritizes agent training and levelling
  - Creates synthetic tests, injects bugs, promotes agents

On human activity:
  - Immediate freeze
  - State saved to Git
  - VRAM released
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional


ACTIVE_IDLE_THRESHOLD_S = 15 * 60  # 15 minutes


class IdleState(str, Enum):
    ACTIVE = "active"            # Human is present
    IDLE = "idle"                # No input > 15 min
    ACTIVE_IDLE = "active_idle"  # In Active Idle Mode (training agents)


class IdleDetector:
    """Monitors human activity and manages idle/active state transitions.

    Usage:
        detector = IdleDetector(on_idle=start_training, on_wake=stop_training)
        detector.mark_activity()  # call on every human input
        detector.start()           # background monitoring thread
    """

    def __init__(
        self,
        threshold_s: int = ACTIVE_IDLE_THRESHOLD_S,
        on_idle: Optional[Callable[[], None]] = None,
        on_wake: Optional[Callable[[], None]] = None,
    ) -> None:
        self.threshold_s = threshold_s
        self._on_idle = on_idle
        self._on_wake = on_wake

        self._last_activity: float = time.time()
        self._state: IdleState = IdleState.ACTIVE
        self._entered_idle_at: Optional[datetime] = None

        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ─── Public API ───────────────────────────────────────────────────────

    def mark_activity(self) -> None:
        """Call this on every human input event."""
        with self._lock:
            was_idle = self._state != IdleState.ACTIVE
            self._last_activity = time.time()

            if was_idle and self._state == IdleState.ACTIVE_IDLE:
                # Waking up from active idle
                self._state = IdleState.ACTIVE
                self._entered_idle_at = None
                if self._on_wake:
                    self._on_wake()
            elif was_idle:
                self._state = IdleState.ACTIVE
                self._entered_idle_at = None

    @property
    def state(self) -> IdleState:
        with self._lock:
            return self._state

    @property
    def idle_seconds(self) -> float:
        """Seconds since last human activity."""
        with self._lock:
            return time.time() - self._last_activity

    @property
    def is_active_idle(self) -> bool:
        return self.state == IdleState.ACTIVE_IDLE

    # ─── Background monitoring ─────────────────────────────────────────────

    def start(self, check_interval_s: float = 5.0) -> None:
        """Start background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(check_interval_s,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _monitor_loop(self, interval_s: float) -> None:
        """Background loop that checks idle threshold."""
        while self._running:
            time.sleep(interval_s)
            with self._lock:
                idle_s = time.time() - self._last_activity

                if self._state == IdleState.ACTIVE and idle_s >= self.threshold_s:
                    # Transition to idle
                    self._state = IdleState.IDLE
                    self._entered_idle_at = datetime.now(timezone.utc)
                    # Immediately escalate to active idle
                    self._state = IdleState.ACTIVE_IDLE
                    if self._on_idle:
                        self._on_idle()

    # ─── Status ───────────────────────────────────────────────────────────

    def status_dict(self) -> dict:
        """Return current status as a dict for logging/telemetry."""
        with self._lock:
            return {
                "state": self._state.value,
                "idle_seconds": round(time.time() - self._last_activity, 1),
                "threshold_s": self.threshold_s,
                "entered_idle_at": (
                    self._entered_idle_at.isoformat() if self._entered_idle_at else None
                ),
            }

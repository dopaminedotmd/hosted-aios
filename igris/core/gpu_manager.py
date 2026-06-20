"""
GPU/VRAM Manager for Commander Igris.

Wraps nvidia-ml-py (pynvml) to:
  - Monitor real-time VRAM usage on RTX 3090
  - Enforce the VRAM budget from the spec (Qwen ~16.5, KV ~6, Embed ~3, Slack ~2 GB)
  - Accept/reject allocation requests from agents
  - Trigger OOM prevention (freeze agents, evict cache) before hitting the limit

The manager is a singleton — only one component owns VRAM decisions.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import pynvml

from igris.models.hardware import GPUAllocation, HardwareProfile, RAMAllocation


# ─── Spec-defined allocation budget for RTX 3090 24 GB ────────────────────────
# Note: KV-cache (50 GB) lives in system RAM (64 GB DDR4), not VRAM.
# These allocations are VRAM-only.

DEFAULT_ALLOCATIONS: list[GPUAllocation] = [
    GPUAllocation(component="qwen-coder-32b", allocated_gb=19.0, min_gb=17.0, max_gb=20.0),
    GPUAllocation(component="embeddings",      allocated_gb=1.2,  min_gb=1.0,  max_gb=2.0),
    GPUAllocation(component="overhead-slack",  allocated_gb=2.0,  min_gb=1.0,  max_gb=2.5),
]


@dataclass
class VRAMSnapshot:
    """Point-in-time VRAM reading."""
    total_gb: float
    used_gb: float
    free_gb: float
    utilization_pct: float
    temperature_c: int
    timestamp: float = field(default_factory=time.time)


class GPUManager:
    """Singleton GPU/VRAM manager for Igris.

    Usage:
        gpu = GPUManager()
        snap = gpu.snapshot()
        ok = gpu.can_allocate("new-model", 2.0)  # returns bool
        gpu.allocate("new-model", 2.0)            # registers allocation
    """

    _instance: Optional["GPUManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "GPUManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        pynvml.nvmlInit()
        self._device_count = pynvml.nvmlDeviceGetCount()
        if self._device_count == 0:
            raise RuntimeError("No NVIDIA GPU detected")
        self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(self._handle)
        if isinstance(gpu_name, bytes):
            gpu_name = gpu_name.decode("utf-8")

        total_mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle).total
        self.hardware = HardwareProfile(
            gpu_name=gpu_name,
            gpu_vram_gb=total_mem / (1024**3),
            allocations=list(DEFAULT_ALLOCATIONS),
            ram_allocations=[
                RAMAllocation(
                    component="kv-cache",
                    allocated_gb=50.0,
                    min_gb=40.0,
                    max_gb=55.0,
                    note="KV-cache offloadad till system-RAM via llama.cpp --no-kv-offload",
                ),
            ],
        )

        self._custom_allocations: dict[str, GPUAllocation] = {}

    # ─── snapshot ─────────────────────────────────────────────────────────

    def snapshot(self) -> VRAMSnapshot:
        """Return current VRAM state from nvidia-ml-py."""
        mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
        temp = pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU)

        return VRAMSnapshot(
            total_gb=mem.total / (1024**3),
            used_gb=mem.used / (1024**3),
            free_gb=mem.free / (1024**3),
            utilization_pct=util.gpu,
            temperature_c=temp,
        )

    # ─── allocation logic ─────────────────────────────────────────────────

    def can_allocate(self, component: str, requested_gb: float) -> bool:
        """Check if `requested_gb` fits within remaining VRAM.

        Note: spec allocations are planning targets, not runtime reservations.
        Only custom allocations count against the hardware limit.
        """
        current = self._custom_allocated_gb
        return (current + requested_gb) <= self.hardware.gpu_vram_gb

    def allocate(self, component: str, requested_gb: float,
                 min_gb: float = 0.0, max_gb: float = 24.0) -> bool:
        """Register a custom allocation. Returns True if successful."""
        if not self.can_allocate(component, requested_gb):
            return False
        alloc = GPUAllocation(
            component=component,
            allocated_gb=requested_gb,
            min_gb=min_gb,
            max_gb=max_gb,
        )
        self._custom_allocations[component] = alloc
        return True

    def deallocate(self, component: str) -> bool:
        """Remove a custom allocation."""
        return self._custom_allocations.pop(component, None) is not None

    @property
    def total_allocated_gb(self) -> float:
        spec_total = sum(a.allocated_gb for a in self.hardware.allocations)
        custom_total = sum(a.allocated_gb for a in self._custom_allocations.values())
        return spec_total + custom_total

    @property
    def _custom_allocated_gb(self) -> float:
        """Sum of only custom (runtime) allocations — what actually counts."""
        return sum(a.allocated_gb for a in self._custom_allocations.values())

    @property
    def free_budget_gb(self) -> float:
        return self.hardware.gpu_vram_gb - self.total_allocated_gb

    # ─── OOM prevention ───────────────────────────────────────────────────

    def check_oom_risk(self) -> dict:
        """Evaluate OOM risk. Returns dict with risk level and recommendation."""
        snap = self.snapshot()
        free_pct = (snap.free_gb / snap.total_gb) * 100

        if free_pct < 5:
            return {"risk": "critical", "free_gb": snap.free_gb,
                    "action": "EVICT_ALL — freeze agents, flush KV cache"}
        elif free_pct < 10:
            return {"risk": "high", "free_gb": snap.free_gb,
                    "action": "reduce_context — trim context window by 50%"}
        elif free_pct < 20:
            return {"risk": "moderate", "free_gb": snap.free_gb,
                    "action": "warn — defer non-critical allocations"}
        return {"risk": "low", "free_gb": snap.free_gb, "action": "none"}

    # ─── lifecycle ────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Release NVML resources."""
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass
        GPUManager._instance = None
        self._initialized = False

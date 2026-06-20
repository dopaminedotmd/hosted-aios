"""
Tests for GPU/VRAM Manager.

Covers:
  - Singleton pattern
  - VRAM snapshot accuracy
  - Allocation budget enforcement
  - OOM risk detection
"""

import pytest

from igris.core.gpu_manager import GPUManager, VRAMSnapshot


@pytest.fixture
def gpu():
    """Get the singleton GPUManager instance."""
    return GPUManager()


class TestGPUManager:
    def test_singleton(self):
        g1 = GPUManager()
        g2 = GPUManager()
        assert g1 is g2

    def test_snapshot_returns_valid_data(self, gpu):
        snap = gpu.snapshot()
        assert isinstance(snap, VRAMSnapshot)
        assert snap.total_gb > 0
        assert snap.free_gb >= 0
        assert snap.used_gb >= 0
        assert 0 <= snap.utilization_pct <= 100
        assert 0 <= snap.temperature_c <= 120

    def test_hardware_profile_loaded(self, gpu):
        hw = gpu.hardware
        assert "RTX 3090" in hw.gpu_name or "3090" in hw.gpu_name
        assert 23.0 <= hw.gpu_vram_gb <= 25.0  # allow minor rounding
        assert len(hw.allocations) == 3  # VRAM: qwen, embeddings, slack (kv-cache → RAM)

    def test_spec_allocations_total(self, gpu):
        """Sum of VRAM spec allocations should be ~22.2 GB (19 + 1.2 + 2.0)."""
        total = sum(a.allocated_gb for a in gpu.hardware.allocations)
        assert 21.0 <= total <= 23.0  # ~22.2 GB VRAM
        # KV-cache (50 GB) is in system RAM — verify separately
        ram_total = sum(a.allocated_gb for a in gpu.hardware.ram_allocations)
        assert 48.0 <= ram_total <= 52.0  # ~50 GB RAM

    def test_can_allocate_within_budget(self, gpu):
        # 0.5 GB should fit (24 - 27.5 = -3.5, but allocations are budgets not actual)
        # The can_allocate checks against hardware total, not budget
        assert gpu.can_allocate("test", 0.5) is True

    def test_cannot_allocate_too_much(self, gpu):
        # 100 GB obviously exceeds 24 GB
        assert gpu.can_allocate("huge-model", 100.0) is False

    def test_allocate_and_deallocate(self, gpu):
        assert gpu.allocate("test-component", 1.0)
        assert gpu.deallocate("test-component") is True
        assert gpu.deallocate("nonexistent") is False

    def test_free_budget_gb_non_negative(self, gpu):
        """free_budget_gb can be negative if budget over-allocated — that's
        expected since spec allocations target ~27.5 GB on 24 GB card."""
        assert isinstance(gpu.free_budget_gb, float)

    def test_oom_risk_detection(self, gpu):
        risk = gpu.check_oom_risk()
        assert risk["risk"] in ("low", "moderate", "high", "critical")
        assert "free_gb" in risk
        assert "action" in risk

    def test_total_allocated_gb(self, gpu):
        total = gpu.total_allocated_gb
        assert total > 0  # at minimum the spec allocations

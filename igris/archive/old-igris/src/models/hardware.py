"""
Hardware profile and GPU allocation models for Commander Igris.

VRAM budget (RTX 3090 24 GB GDDR6X):
  - Qwen2.5-Coder-32B:        ~16.5 GB
  - Embeddings (BGE-M3):       ~3.0 GB
  - Overhead/Slack:            ~2.0 GB
  - Free for agents:           ~2.5 GB

System RAM budget (64 GB DDR4):
  - KV-Cache (64k context):   ~50.0 GB  (offloaded via llama.cpp --no-kv-offload)
  - OS + Docker + overhead:   ~14.0 GB
"""

from pydantic import BaseModel, Field


class GPUAllocation(BaseModel):
    """VRAM or RAM budget for a single component."""

    component: str = Field(..., description="e.g. 'qwen-coder-32b', 'kv-cache', 'embeddings'")
    allocated_gb: float = Field(..., ge=0.0, description="Allocated memory in GiB")
    min_gb: float = Field(default=0.0, ge=0.0, description="Minimum needed")
    max_gb: float = Field(default=0.0, ge=0.0, description="Hard cap")


class RAMAllocation(BaseModel):
    """System RAM allocation (DDR4, not VRAM)."""

    component: str = Field(..., description="e.g. 'kv-cache', 'docker-overhead'")
    allocated_gb: float = Field(..., ge=0.0)
    min_gb: float = Field(default=0.0, ge=0.0)
    max_gb: float = Field(default=0.0, ge=0.0)
    note: str = Field(default="")


class HardwareProfile(BaseModel):
    """Immutable snapshot of the host hardware, validated once at startup."""

    cpu_model: str = Field(default="AMD Ryzen 9 3950X")
    cpu_cores: int = Field(default=16)
    cpu_threads: int = Field(default=32)
    ram_gb: float = Field(default=64.0)
    gpu_name: str = Field(default="NVIDIA GeForce RTX 3090")
    gpu_vram_gb: float = Field(default=24.0)
    max_context_tokens: int = Field(default=65536, description="KV cache context window — 64k")
    allocations: list[GPUAllocation] = Field(default_factory=list)
    ram_allocations: list[RAMAllocation] = Field(default_factory=list)

    @property
    def total_allocated_gb(self) -> float:
        return sum(a.allocated_gb for a in self.allocations)

    @property
    def free_vram_gb(self) -> float:
        return self.gpu_vram_gb - self.total_allocated_gb

    @property
    def total_ram_allocated_gb(self) -> float:
        return sum(a.allocated_gb for a in self.ram_allocations)

    @property
    def free_ram_gb(self) -> float:
        return self.ram_gb - self.total_ram_allocated_gb

    def fits(self, allocation: GPUAllocation) -> bool:
        """Check if a new VRAM allocation fits within remaining VRAM."""
        return (self.total_allocated_gb + allocation.allocated_gb) <= self.gpu_vram_gb

    def ram_fits(self, allocation: RAMAllocation) -> bool:
        """Check if a new RAM allocation fits within remaining system RAM."""
        return (self.total_ram_allocated_gb + allocation.allocated_gb) <= self.ram_gb

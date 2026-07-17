"""Legacy memory manager - deprecated, use memory_service instead."""

from __future__ import annotations

from memory.memory_service import MemoryService

# Re-export for backward compatibility
MemoryManager = MemoryService

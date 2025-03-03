"""Long-term memory management for Moana."""

import os
from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager, ReflectionExecutor

from .models import Memory


# Get model names from environment variables with defaults
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "openai:text-embedding-3-small")
MEMORY_MODEL = os.environ.get("MEMORY_MODEL", "anthropic:claude-3-5-sonnet-latest")

# Initialize memory store
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": EMBEDDING_MODEL,
    }
)

# Create memory manager to extract memories from conversations
memory_manager = create_memory_store_manager(
    MEMORY_MODEL,
    # Store memories in the "memories" namespace
    namespace=("{user_id}", "memories"),
    schemas=[Memory],
    instructions="Extract user preferences and any other useful information. If a memory conflicts with an existing one, then just update it",
)

# Wrap memory_manager with ReflectionExecutor for deferred processing
executor = ReflectionExecutor(memory_manager) 
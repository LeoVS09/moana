"""Long-term memory management for Moana."""

from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager, ReflectionExecutor

from memory.models import Memory


# Initialize memory store
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small",
    }
)

# Create memory manager to extract memories from conversations
memory_manager = create_memory_store_manager(
    "anthropic:claude-3-5-sonnet-latest",
    # Store memories in the "memories" namespace
    namespace=("{user_id}", "memories"),
    schemas=[Memory],
    instructions="Extract user preferences and any other useful information. If a memory conflicts with an existing one, then just update it",
)

# Wrap memory_manager with ReflectionExecutor for deferred processing
executor = ReflectionExecutor(memory_manager) 
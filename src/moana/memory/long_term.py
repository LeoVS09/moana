"""Long-term memory management for Moana."""

import os
from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager, ReflectionExecutor

from .models import Memory, Profile, Triple


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

# Human-readable free format contectual memory
# Usefull as backup for other types of memories, but cannot store big amounts of data
# Have better search capabilities than triples
memories_manager = create_memory_store_manager(
    MEMORY_MODEL,
    # Store memories in the "memories" namespace
    namespace=("{user_id}", "memories"),
    schemas=[Memory],
    instructions=("Extract user preferences and any other useful information." 
                  "If a memory conflicts with an existing one, then just update it"),
)

# Wrap memorys_manager with ReflectionExecutor for deferred processing
memories_executor = ReflectionExecutor(memories_manager) 

# Machine-readable triples based semantic memory
# Graph based memory that good for reasoning, planning and deduction
triples_manager = create_memory_store_manager(
    MEMORY_MODEL,
    namespace=("{user_id}", "triples"),
    schemas=[Triple],
    instructions=("Store all new facts, preferences, and relationships as triples."
                  "If a memory conflicts with an existing one, then just update it"),
)

# Wrap triples_manager with ReflectionExecutor for deferred processing
triples_executor = ReflectionExecutor(triples_manager) 

# Semantic profile memory
profile_manager = create_memory_store_manager(
    MEMORY_MODEL,
    namespace=("{user_id}", "profile"),
    schemas=[Profile],
    instructions=("Extract user profile information."
                  "Try to fill profile with as much information as possible"
                  "Use only avaiable information do not imagine anything"
                  "If you cannot find any information, then just set as Unknown"
                  "If it exists, then just update it when need only"
                  ),
)

# Wrap profile_manager with ReflectionExecutor for deferred processing
profile_executor = ReflectionExecutor(profile_manager) 
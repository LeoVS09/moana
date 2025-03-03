"""Subconscious memory operations for Moana."""

from typing import Dict, List, Any
from langgraph.config import get_store
from moana.memory.long_term import executor
from moana.state import State
from moana.configuration import Configuration

async def recall(configuration: Configuration, state: State, limit: int = 10) -> str:
    """Retrieve and format relevant memories.
    
    Args:
        user_id (str): The user ID to retrieve memories for.
        recent_messages_content (List[str]): Content from recent messages to use as query.
        limit (int): Maximum number of memories to retrieve.
        
    Returns:
        str: Formatted memories string ready for inclusion in prompts.
    """

    # Retrieve relevant memories for context
    recent_messages_content = [m.content for m in state.messages[-3:] if hasattr(m, 'content')]
    
    memories = await retrieve_relevant_memories(configuration.user_id, recent_messages_content, limit)

    return format_memories(memories)


async def retrieve_relevant_memories(user_id: str, recent_messages_content: List[str], limit: int = 10):
    """Retrieve relevant memories based on recent message content."""
    store = get_store()
    memories = await store.asearch(
        (user_id, "memories"),
        query=str(recent_messages_content),
        limit=limit,
    )
    return memories

def format_memories(memories: List[Any]) -> str:
    """Format memories for inclusion in the prompt."""
    if not memories:
        return ""
        
    memory_entries = "\n".join(f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories)
    return f"""
<memories>
{memory_entries}
</memories>"""


def memorize(state: State, system_message: str, response_content: str, delay: float = 0.5):
    """Process a conversation to extract and store memories.
    
    Args:
        system_message (str): The system message.
        messages (List[Dict]): The conversation messages.
        response_content (str): The assistant's response content.
        delay (float): Delay in seconds before processing.
    """
    to_process = {
        "messages": [
            {"role": "system", "content": system_message},
            *[{"role": m.type, "content": m.content} for m in state.messages],
            {"role": "assistant", "content": response_content},
        ]
    }
    
    # Use the executor to schedule memory processing with a delay
    executor.submit(to_process, after_seconds=delay) 
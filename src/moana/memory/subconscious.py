"""Subconscious memory operations for Moana."""

from typing import List, Any
from langgraph.config import get_store
from .long_term import memories_executor, triples_executor, profile_executor
from moana.state import State
from moana.configuration import Configuration

async def recall(configuration: Configuration, state: State) -> str:
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
    
    # Retrieve human-readable memories, can be long and verbose, but probably have better context
    memories = await retrieve_relevant_memories(configuration.user_id, "memories", recent_messages_content, limit=3)

    # Retrieve machine-readable memories, can be short and concise, but probably harder to find relevant ones
    triples = await retrieve_relevant_memories(configuration.user_id, "triples", recent_messages_content, limit=20)

    # Retrieve user profile
    profile = await retrieve_user_profile(configuration.user_id)

    return format_memories(memories, triples, profile)


async def retrieve_relevant_memories(user_id: str, namespace: str, messages: List[str], limit: int = 10):
    """Retrieve relevant memories based on recent message content."""
    store = get_store()
    memories = await store.asearch(
        (user_id, namespace),
        query=str(messages),
        limit=limit,
    )
    return memories

async def retrieve_user_profile(user_id: str) -> str:
    """Retrieve user profile from memory.
    
    Args:
        user_id (str): The user ID to retrieve profile for.
        
    Returns:
        str: Formatted user profile string or None if not found.
    """
    store = get_store()
    results = await store.asearch(
        (user_id, "profile"),
    )

    if results:
        return f"""<User Profile>:

{results[0].value}
</User Profile>
"""
    return None

def format_entry_block(entries: List[Any], tag: str) -> str:
    """Format a list of memory entries with a specific tag.
    
    Args:
        entries (List[Any]): List of memory entries with key, value, and score attributes
        tag (str): Tag name for the XML-like wrapper
        
    Returns:
        str: Formatted string with entries wrapped in the specified tag
    """
    if not entries:
        return ""
        
    formatted_entries = "\n".join(f"[{entry.key}]: {entry.value} (similarity: {entry.score})" for entry in entries)
    return f"""
<{tag}>
{formatted_entries}
</{tag}>"""


def format_memories(memories: List[Any], triples: List[Any], profile: str = None) -> str:
    """Format memories for inclusion in the prompt.
    
    Args:
        memories (List[Any]): List of memory entries
        triples (List[Any]): List of knowledge triple entries
        profile (str, optional): Formatted user profile string
        
    Returns:
        str: Formatted memories string
    """
    result = ""
    
    if profile:
        result += profile
    
    if memories:
        result += format_entry_block(memories, "memories")
    
    if triples:
        result += format_entry_block(triples, "knowledge")
    
    return result


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
    
    # Use the executors to schedule memory processing with a delay
    # Save contextual memory
    memories_executor.submit(to_process, after_seconds=delay) 
    # Save semantic memory
    triples_executor.submit(to_process, after_seconds=delay) 
    # Save semantic profile memory
    profile_executor.submit(to_process, after_seconds=delay) 
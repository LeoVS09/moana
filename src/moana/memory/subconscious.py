"""Subconscious memory operations for Moana."""

from typing import List, Any
from langgraph.config import get_store
from langgraph.graph import MessagesState
from .long_term import memories_executor, triples_executor, profile_executor, episodes_executor
from moana.configuration import Configuration
from datetime import datetime, timezone

MEMORY_TEMPLATE = """{memories}

System time: {system_time}"""

async def recall(configuration: Configuration, state: MessagesState) -> str:
    """Retrieve and format relevant memories.
    
    Args:
        user_id (str): The user ID to retrieve memories for.
        recent_messages_content (List[str]): Content from recent messages to use as query.
        limit (int): Maximum number of memories to retrieve.
        
    Returns:
        str: Formatted memories string ready for inclusion in prompts.
    """

    # Retrieve relevant memories for context
    recent_messages_content = [m.content for m in state['messages'][-3:] if hasattr(m, 'content')]
    

    user_id = configuration.user_id if configuration.user_id else 'default'

    # Retrieve human-readable memories, can be long and verbose, but probably have better context
    memories = await retrieve_relevant_memories(user_id, "memories", recent_messages_content, limit=3)

    # Retrieve machine-readable memories, can be short and concise, but probably harder to find relevant ones
    triples = await retrieve_relevant_memories(user_id, "triples", recent_messages_content, limit=20)

    # Retrieve episodic memories, long and verbose, but can be usefull for reasoning
    episodes = await retrieve_relevant_memories(user_id, "episodes", recent_messages_content, limit=1)

    # Retrieve user profile
    profile = await retrieve_user_profile(user_id)

    memories = format_memories(memories, triples, episodes, profile)

    # Format the system prompt with memories and current time
    return MEMORY_TEMPLATE.format(
        system_time=datetime.now(tz=timezone.utc).isoformat(),
        memories=memories
    )



async def retrieve_relevant_memories(user_id: str, namespace: str, messages: List[str], limit: int = 10):
    """Retrieve relevant memories based on recent message content."""
    store = get_store()
    memories = await store.asearch(
        (user_id, namespace),
        query=str(messages),
        limit=limit,
    )
    print('memories', user_id, namespace, memories)
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


def format_memories(memories: List[Any], triples: List[Any], episodes: List[Any], profile: str = None) -> str:
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
    
    if episodes:
        result += '\n\n <Episodic Memories>'
        for i, item in enumerate(episodes, start=1):
            episode = item.value["content"]
            result += f"""

Episode {i}:
When: {episode['observation']}
Thought: {episode['thoughts']}
Did: {episode['action']}
Result: {episode['result']}
        """
        
        result += '</Episodic Memories>'

    return result


def memorize(state: MessagesState):
    """
    Process a conversation to extract and store memories.
    """
    to_process = {
        "messages": [
            *[{"role": m.type, "content": m.content} for m in state['messages']],
        ]
    }
    
    # Use the executors to schedule memory processing with a delay
    # Save contextual memory
    memories_executor.submit(to_process, after_seconds=0.5) 
    # Save semantic memory
    triples_executor.submit(to_process, after_seconds=0.5) 
    # Save semantic profile memory
    profile_executor.submit(to_process, after_seconds=0.5) 
    # Save episodic memory
    episodes_executor.submit(to_process, after_seconds=0.5) 
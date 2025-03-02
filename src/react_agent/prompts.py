from langgraph.utils.config import get_store 

"""Default prompts used by the agent."""

SYSTEM_PROMPT = """You are a helpful AI assistant.

System time: {system_time}"""

async def prompt(state):
    """Prepare the messages for the LLM."""
    # Get store from configured contextvar; 
    store = get_store() # Same as that provided to `create_react_agent`
    memories = await store.asearch(
        # Search within the same namespace as the one
        # we've configured for the agent
        ("memories",),
        query=state["messages"][-1].content,
    )
    system_msg = f"""You are a helpful assistant.

## Memories
<memories>
{memories}
</memories>
"""
    return [{"role": "system", "content": system_msg}, *state["messages"]]


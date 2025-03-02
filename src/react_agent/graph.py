from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from react_agent import prompts

# Set up storage 
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small",
    }
) 

checkpointer = MemorySaver() # Checkpoint graph state

# Create an agent with memory capabilities 
graph = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",
    prompt=prompts.prompt,
    tools=[
        # Add memory tools 
        # The agent can call "manage_memory" to
        # create, update, and delete memories by ID
        # Namespaces add scope to memories. To
        # scope memories per-user, do ("memories", "{user_id}"):
        create_manage_memory_tool(namespace=("memories",)),
    ],
    store=store,
    checkpointer=checkpointer,
)
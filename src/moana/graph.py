"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langgraph.config import get_store
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager, ReflectionExecutor

from moana.configuration import Configuration
from moana.state import InputState, State
from moana.tools import TOOLS
from moana.utils import load_chat_model
from pydantic import BaseModel, Field

# Initialize memory store
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small",
    }
)

class Memory(BaseModel): # 
    """Memories about new facts, preferences, and relationships."""
    content: str = Field(..., description="The main content of the memory. For example:'User expressed interest in learning about French.'")
    context: str = Field(..., description="Additional context for the memory. For example:'This was mentioned while discussing career options in Europe.'")
    confidence: str = Field(..., description="The confidence in memory accuracy. For example: 'high', 'medium', 'low'")


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

# Define the function that calls the model
async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(configuration.model).bind_tools(TOOLS)

    # Retrieve relevant memories for context
    recent_messages_content = [m.content for m in state.messages[-3:] if hasattr(m, 'content')]
    
    s = get_store() # direct store access not work, need retrive it through function
    memories = await s.asearch(
        (configuration.user_id, "memories"),
        query=str(recent_messages_content),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted_memories = ""
    if memories:
        memory_entries = "\n".join(f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories)
        formatted_memories = f"""
<memories>
{memory_entries}
</memories>"""

    # Format the system prompt with memories and current time
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat(),
        user_info=formatted_memories
    )

    print(system_message)
    
    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages], config
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        response = AIMessage(
            id=response.id,
            content="Sorry, I could not find an answer to your question in the specified number of steps.",
        )

    # Extract and store memories from the conversation
    to_process = {
        "messages": [
            {"role": "system", "content": system_message},
            *[{"role": m.type, "content": m.content} for m in state.messages],
            {"role": "assistant", "content": response.content},
        ]
    }
    
    # Use the executor to schedule memory processing with a delay
    # This allows for more efficient batching of memory operations
    # Half a second delay - adjust based on your application needs
    executor.submit(to_process, after_seconds=0.5)

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


# Define a new graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
    store=store,  # Add the memory store to the graph
)
graph.name = "Moana"  # This customizes the name in LangSmith

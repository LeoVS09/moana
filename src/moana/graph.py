"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
import os
from typing import Dict, List, Literal, cast, Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph import MessagesState
from langgraph.store.memory import BaseStore

from moana.configuration import Configuration
from moana.tools import TOOLS
from moana.utils import load_chat_model

# Import memory-related functionality
from moana.memory import store, recall, memorize, checkpointer

MODEL = os.environ.get("MODEL", "anthropic:claude-3-5-sonnet-latest")


agent = create_react_agent(
    MODEL,
    tools=TOOLS,
    store=store,
    checkpointer=checkpointer,
    config_schema=Configuration
)

async def prepare_memories(state: MessagesState, store: BaseStore, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    print(state)

    # Get and format relevant memories
    memories = await recall(configuration, state)

    # Format the system prompt with memories and current time
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat(),
        user_info=memories
    )

    print(system_message)

    # Check if there's already a system message and update it instead of adding a new one
    messages = state["messages"]
    
    # Create a new system message
    system_msg = {"role": "system", "content": system_message}
    
    # Check if the first message is a system message
    if messages and hasattr(messages[0], 'type') and messages[0].type == "system":
        # Replace the first message with our new system message
        return {
            "messages": [system_msg] + state["messages"][1:]
        }
    else:
        # Add the system message at the beginning
        return {
            "messages": [system_msg] + state["messages"]
        }


def memorize_conversation(state: MessagesState):
    memorize(state)
    return state

# Define a new graph
builder = StateGraph(MessagesState, config_schema=Configuration)

builder.add_node("prepare_memories", prepare_memories)
builder.add_node("agent", agent)
builder.add_node("memorize_conversation", memorize_conversation)

# Set the entrypoint as `agent`
# This means that this node is the first one called
builder.add_edge(START, "prepare_memories")
builder.add_edge("prepare_memories", "agent")
builder.add_edge("agent", "memorize_conversation")
builder.add_edge("memorize_conversation", END)

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
    store=store,  # Add the memory store to the graph
    checkpointer=checkpointer
)

graph.name = "Moana"  # This customizes the name in LangSmith

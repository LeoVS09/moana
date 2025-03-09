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
from moana.prompts import SYSTEM_PROMPT
from moana.tools import TOOLS
from moana.utils import load_chat_model
from moana.state import State

# Import memory-related functionality
from moana.memory import store, recall, memorize, checkpointer

MODEL = os.environ.get("MODEL", "anthropic:claude-3-5-sonnet-latest")


agent = create_react_agent(
    MODEL,
    tools=TOOLS,
    store=store,
    checkpointer=checkpointer,
    config_schema=Configuration,
    prompt=SYSTEM_PROMPT
)

async def prepare_memories(state: State, store: BaseStore, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    print(state)

    # Get and format relevant memories
    memory_message = await recall(configuration, state)
    print(memory_message)
    
    return {
        "memories": memory_message
    }

def call_agent(state: State):
    # Create a new system message with memories
    system_msg = {"role": "system", "content": state["memories"]}
    
    # Prepare messages with the system message containing memories
    agent_messages = state["messages"] + [system_msg]
    
    # Invoke the agent with the prepared messages
    response = agent.invoke({"messages": agent_messages})
    
    # Add agent message as last
    return {"messages": state["messages"] + response["messages"][-1:]}

def memorize_conversation(state: State):
    memorize(state)
    return state

# Define a new graph
builder = StateGraph(State, config_schema=Configuration)

builder.add_node("prepare_memories", prepare_memories)
builder.add_node("agent", call_agent)
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

"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
import os

from typing import Callable, Dict, List, Literal, cast, Any, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph import MessagesState
from langgraph.store.memory import BaseStore
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph_swarm.handoff import get_handoff_destinations
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from typing_extensions import Annotated

from moana.configuration import Configuration
from moana.prompts import SYSTEM_PROMPT
from moana.tools import TOOLS
from moana.utils import load_chat_model
from moana.state import State
from moana.agent import create_agent_node, create_handoff_to_agent

# Import memory-related functionality
from moana.memory import store, recall, memorize, checkpointer

MODEL = os.environ.get("MODEL", "anthropic:claude-3-5-sonnet-latest")


async def prepare_memories(state: State, store: BaseStore, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    # Get and format relevant memories
    memory_message = await recall(configuration, state)
    
    return {
        "memories": memory_message
    }

@tool(description="Finish the conversation if you spoken and not need to call other agents")
def finish_conversation(tool_call_id: Annotated[str, InjectedToolCallId]):
    print("Finishing the conversation")
    tool_message = ToolMessage(
        content=f"Finishing the conversation",
        name='finish_conversation',
        tool_call_id=tool_call_id,
    )
    return Command(
        goto='memorize_conversation',
        graph=Command.PARENT,
        update={"messages": [tool_message] },
    )

def make_prompt(base_system_prompt: str, finish_system_prompt: Optional[str] = None) -> Callable[[State, RunnableConfig], list]:
    additional_prompt = []

    if finish_system_prompt is not None:
        additional_prompt = [{"role": "system", "content": finish_system_prompt }]
    
    def prepare_prompt(state: State, config: RunnableConfig):
        return [
            {"role": "system", "content": base_system_prompt}, 
            {"role": "system", "content": state["memories"]}, 
            *state["messages"],
            *additional_prompt
            ]
    
    return prepare_prompt



# Create the assistant agent and node
_, assistant_node = create_agent_node(
    model=MODEL,
    name="Assistant",
    tools=TOOLS + [
        create_handoff_to_agent(
            agent_name="Joker", 
            description="Before saying something to the user, ask Joker agent for a joke"
        ), 
        finish_conversation
    ],
    store=store,
    checkpointer=checkpointer,
    state_schema=State,
    config_schema=Configuration,
    prompt=make_prompt(SYSTEM_PROMPT, "ALLWAYS before answering to user, ask Joker for a joke on current topic and when he reply rephrase joke to the user and continue conversation"),
    destinations=["Joker", "memorize_conversation"],
    default_destination="memorize_conversation"
)

# Create the joker agent and node
_, joker_node = create_agent_node(
    model=MODEL,
    name="Joker",
    tools=TOOLS + [
        create_handoff_to_agent(
            agent_name="Assistant",
            description="After joking, transfer the conversation to the Assistant agent"
        )
    ],
    store=store,
    checkpointer=checkpointer,
    state_schema=State,
    config_schema=Configuration,
    prompt=make_prompt('''
    You are a joker. Joke something funny and realted to the topic of the conversation. You are allowed to joke about the user, the conversation, or the topic and be toxic but funny.
    '''),
    destinations=["Assistant", "memorize_conversation"],
    default_destination="Assistant"
)

def memorize_conversation(state: State):
    memorize(state)
    return state

# Define a new graph
builder = StateGraph(State, config_schema=Configuration)

builder.add_node("prepare_memories", prepare_memories)

# Add agent nodes to the graph
builder.add_node("Assistant", assistant_node, destinations=tuple(["Joker", "memorize_conversation"]))
builder.add_node("Joker", joker_node, destinations=tuple(["Assistant", "memorize_conversation"]))

builder.add_node("memorize_conversation", memorize_conversation)

# Set the entrypoint as `agent`
# This means that this node is the first one called
builder.add_edge(START, "prepare_memories")

builder.add_edge("prepare_memories", "Assistant")

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

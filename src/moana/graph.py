"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
import os
from typing import Callable, Dict, List, Literal, cast, Any

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

# Import memory-related functionality
from moana.memory import store, recall, memorize, checkpointer

MODEL = os.environ.get("MODEL", "anthropic:claude-3-5-sonnet-latest")


async def prepare_memories(state: State, store: BaseStore, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    print(state)

    # Get and format relevant memories
    memory_message = await recall(configuration, state)
    print(memory_message)
    
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

def make_prompt(base_system_prompt: str) -> Callable[[State, RunnableConfig], list]:
    def prepare_prompt(state: State, config: RunnableConfig):
        return [{"role": "system", "content": base_system_prompt}, {"role": "system", "content": state["memories"]}, *state["messages"]]
    
    return prepare_prompt

assistent = create_react_agent(
    MODEL,
    name="Assistent",
    # TODO: not working properly, each agent need choose between saying somthing or transfering the conversation to the other agent. 
    #  As a result there no interaction between the agents. Only one agent at one turn is working
    #  Need make them be able to do both things, say and transfer the conversation and then return back. 
    #  Also finishing covneration tool not working. 
    #  After agent say somthing graph is finished, but need find a way to call memorize_conversation at the end of the conversation
    tools=TOOLS + [create_handoff_tool(
        agent_name="Joker", 
        description="Before saying something to the user, ask Joker agent for a joke"
    ), finish_conversation], 
    store=store,
    checkpointer=checkpointer,
    state_schema=State,
    config_schema=Configuration,
    prompt=make_prompt(SYSTEM_PROMPT)
)

joker = create_react_agent(
    MODEL,
    name="Joker",
    tools=TOOLS + [create_handoff_tool(
        agent_name="Assistent",
        description="After joking, transfer the conversation to the Assistent agent"
    )],
    store=store,
    checkpointer=checkpointer,
    state_schema=State,
    config_schema=Configuration,
    prompt=make_prompt('''
    You are a joker. Joke something funny and realted to the topic of the conversation. You are allowed to joke about the user, the conversation, or the topic and be toxic but funny.
    '''
    )
)

def memorize_conversation(state: State):
    memorize(state)
    return state

# Define a new graph
builder = StateGraph(State, config_schema=Configuration)

builder.add_node("prepare_memories", prepare_memories)

agents = [assistent, joker]

for agent in agents:
    builder.add_node(
        agent.name,
        agent,
        destinations=tuple(list(get_handoff_destinations(agent)) + ["memorize_conversation"]),
    )

builder.add_node("memorize_conversation", memorize_conversation)

# Set the entrypoint as `agent`
# This means that this node is the first one called
builder.add_edge(START, "prepare_memories")

def make_router(default_active_agent: str):
    def route_to_active_agent(state: dict):
        return state.get("active_agent", default_active_agent)
    
    return route_to_active_agent

builder.add_conditional_edges("prepare_memories", make_router("Assistent"), path_map=([agent.name for agent in agents] + ["memorize_conversation"]))

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

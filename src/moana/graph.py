"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
import os

from typing import Callable, Dict, List, Literal, cast, Any, Optional

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.store.memory import BaseStore

from moana.configuration import Configuration
from moana.prompts import SYSTEM_PROMPT
from moana.tools import TOOLS
from moana.state import State
from moana.agent import create_agent_node

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


def make_prompt(
        base_system_prompt: str, 
        finish_system_prompt: Optional[str] = None, 
        destinations: Optional[List[str]] = None,
        include_memories: bool = True,
        only_last_ai_message: bool = False
    ) -> Callable[[State, RunnableConfig], list]:
    """Create a prompt generator for the reactive agent .
    
    Args:
        base_system_prompt: The base system prompt for the agent
        finish_system_prompt: The system prompt for the agent when the conversation is finished
        destinations: Optional list of possible agent to handoff the conversation to. The name of the agent to handoff control to, i.e.
            the name of the agent node in the multi-agent graph.
            Agent names should be simple, clear and unique, preferably in snake_case,
            although you are only limited to the names accepted by LangGraph
            nodes as well as the tool names accepted by LLM providers
        
    Returns:
        A function that generates the prompt for the agent
    """

    starting_prompts = [SystemMessage(content=base_system_prompt)]

    if destinations:
        starting_prompts.append(SystemMessage(content=f"You can handoff the conversation to one of the following agents: {', '.join(destinations)}"))

    ending_prompts = []

    if finish_system_prompt is not None:
        ending_prompts = [SystemMessage(content=finish_system_prompt)]
    
    def prepare_prompt(state: State, config: RunnableConfig):

        if include_memories:
            starting_prompts.append(SystemMessage(content=state["memories"]))

        last_ai_message = None
        for message in reversed(state["messages"]):
            if message.type == "ai":
                last_ai_message = message
                break

        # If it agent-to-agent communication whole dialog can confuse the model
        # so we only include the last AI message
        # agent usally confused when assistent ask him something, so need frame it as user question
        middle_prompts = [HumanMessage(content=last_ai_message.content)] if only_last_ai_message else state["messages"]

        return [
            *starting_prompts,
            *middle_prompts,
            *ending_prompts
        ]
    
    return prepare_prompt


# Create the assistant agent and node
assistant_node = create_agent_node(
    name="Assistant",
    make_prompt=make_prompt(
        SYSTEM_PROMPT, 
        "ALLWAYS before answering to user, ask Joker for a joke on current topic and when he reply rephrase joke to the user and continue conversation",
        ["Joker"]),
    end_destination="memorize_conversation"
)

# TODO: need make it more generic, so new agents can be predifined or added on the fly
# Create the joker agent and node
joker_node = create_agent_node(
    name="Joker",
    make_prompt=make_prompt(
        "You are a agent with name Joker! Joke something funny and realted to the topic of the conversation. You are allowed to joke about the user, the conversation, or the topic and be toxic but funny. Do what the Assistent asks you! Assistant is not your assistent, but the user's assistent.",
        "ALLWAYS write a joke in messageToAgent field and transfering the conversation to the Assistant agent, do NOT END the conversation.",
        ["Assistant"],
        include_memories=False,
        only_last_ai_message=True
        ),
    end_destination="memorize_conversation"
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

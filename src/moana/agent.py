"""Define a wrapper for creating reactive agents and their corresponding nodes.

This module provides a function to create a reactive agent and wrap it in a node function
that can be used in a LangGraph.
"""

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union, cast
import re

from langchain_core.messages import AIMessage, HumanMessage, AnyMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.store.memory import BaseStore
from langgraph.types import Checkpointer

from moana.state import State


def create_agent_node(
    model: str,
    name: str,
    tools: List[BaseTool],
    store: Optional[BaseStore] = None,
    checkpointer: Optional[Checkpointer] = None,
    state_schema: Type = State,
    config_schema: Optional[Type] = None,
    prompt: Optional[Callable] = None,
    destinations: Optional[List[str]] = None,
    default_destination: str = "END",
) -> Tuple[Any, Callable]:
    """Create a reactive agent and wrap it in a node function.
    
    Args:
        model: The model to use for the agent
        name: The name of the agent
        tools: The tools available to the agent
        store: Optional memory store for the agent
        checkpointer: Optional checkpointer for the agent
        state_schema: The state schema for the agent
        config_schema: Optional configuration schema for the agent
        prompt: Optional prompt function for the agent
        destinations: Optional list of possible destinations for the node
        default_destination: Default destination if no handoff is detected
        
    Returns:
        A tuple containing the agent and the node function
    """
    # Create the reactive agent
    agent = create_react_agent(
        model,
        name=name,
        tools=tools,
        store=store,
        checkpointer=checkpointer,
        state_schema=state_schema,
        config_schema=config_schema,
        prompt=prompt
    )
    
    # Define the node function that wraps the agent
    # We use Command[Any] to indicate it can go to any destination
    def agent_node(state: State) -> Command[Any]:
        # Invoke the agent with the current state
        result = agent.invoke(state)
        
        # Check if the last message indicates a handoff to another agent
        if destinations and len(result["messages"]) > 0:
            last_message = result["messages"][-1]

            print("last_message", last_message)
            

            # If the last message is an AIMessage, check for handoff
            if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls"):
                # TODO: Not really work, create_react_agent handles tool calls inside and doesn't output them
                #  But if using handoff tool instead of command, conversation allways returns to previus agent and cannot be continued between agents
                #  Need make conversation to continue between agents as much as it need, and last agent should be able to reply at the end to user
                for tool_call in last_message.tool_calls:
                    # Check if the tool call is a handoff
                    if tool_call.get("name", "").startswith("handoff_to_"):
                        # Extract the destination from the handoff tool name
                        destination = tool_call.get("name", "").replace("handoff_to_", "")
                        if destination in destinations:
                            goto = destination
                            return Command(
                                goto=destination,
                                update={
                                    # NOTE: it's important to insert a tool message here because LLM providers are expecting
                                    # all AI messages to be followed by a corresponding tool result message
                                    "messages": [*result["messages"], {
                                        "role": "tool",
                                        "content": f"Successfully transferred to {goto}",
                                        "tool_call_id": tool_call["id"],
                                        "additional_kwargs": tool_call["args"]
                                    }]
                                }
                            )
        
        # Add system message as last message after assistent
        # This ensures compatibility with providers that don't allow AI messages
        # at the last position of the input messages list
        if result["messages"] and isinstance(result["messages"][-1], AIMessage):
            result["messages"].append(
                {"role": "system", "content": f"Agent {name} finished their turn"}
            )
        
        # Return the command with the updated state and next destination
        return Command(
            update={
                # Share the agent's message history with other agents
                "messages": result["messages"],
            },
            goto=default_destination,
        )
    
    # Return both the agent and the node function
    return agent, agent_node 



WHITESPACE_RE = re.compile(r"\s+")
METADATA_KEY_HANDOFF_DESTINATION = "__handoff_destination"

def _normalize_agent_name(agent_name: str) -> str:
    """Normalize an agent name to be used inside the tool name."""
    return WHITESPACE_RE.sub("_", agent_name.strip())

def create_handoff_to_agent(*, agent_name: str, description: str | None = None) -> BaseTool:
    """Create a tool that can handoff control to the requested agent.

    Args:
        agent_name: The name of the agent to handoff control to, i.e.
            the name of the agent node in the multi-agent graph.
            Agent names should be simple, clear and unique, preferably in snake_case,
            although you are only limited to the names accepted by LangGraph
            nodes as well as the tool names accepted by LLM providers
            (the tool name will look like this: `transfer_to_<agent_name>`).
        description: Optional description for the handoff tool.
    """
    name = f"transfer_to_{_normalize_agent_name(agent_name)}"
    if description is None:
        description = f"Transfer conversation to the '{agent_name}'"

    @tool(name, description=description)
    def handoff_to_agent(messageToAgent: str):
        # This tool is not returning anything: we're just using it
        # as a way for LLM to signal that it needs to hand off to another agent
        return

    handoff_to_agent.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
    return handoff_to_agent
"""Define a wrapper for creating reactive agents and their corresponding nodes.

This module provides a function to create a reactive agent and wrap it in a node function
that can be used in a LangGraph.
"""

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union, cast

from langchain_core.messages import AIMessage, HumanMessage, AnyMessage
from langchain_core.tools import BaseTool
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
        
        # Determine the next destination
        goto = default_destination
        
        # Check if the last message indicates a handoff to another agent
        if destinations and len(result["messages"]) > 0:
            last_message = result["messages"][-1]
            
            # If the last message is an AIMessage, check for handoff
            if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls"):
                for tool_call in last_message.tool_calls:
                    # Check if the tool call is a handoff
                    if tool_call.get("name", "").startswith("handoff_to_"):
                        # Extract the destination from the handoff tool name
                        destination = tool_call.get("name", "").replace("handoff_to_", "")
                        if destination in destinations:
                            goto = destination
                            break
        
        # Wrap the last message in a human message with the agent's name
        # This ensures compatibility with providers that don't allow AI messages
        # at the last position of the input messages list
        if result["messages"] and isinstance(result["messages"][-1], AIMessage):
            result["messages"][-1] = HumanMessage(
                content=result["messages"][-1].content,
                name=name.lower()
            )
        
        # Return the command with the updated state and next destination
        return Command(
            update={
                # Share the agent's message history with other agents
                "messages": result["messages"],
            },
            goto=goto,
        )
    
    # Return both the agent and the node function
    return agent, agent_node 
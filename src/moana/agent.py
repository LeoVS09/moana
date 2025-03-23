"""Define a wrapper for creating reactive agents and their corresponding nodes.

This module provides a function to create a reactive agent and wrap it in a node function
that can be used in a LangGraph.
"""

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union, cast
import re

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.store.memory import BaseStore
from langgraph.types import Checkpointer
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig

from moana.configuration import Configuration
from moana.state import State
from moana.utils import load_chat_model

class EndConversation(BaseModel):
    """Action to end the conversation."""
    
    response: str = Field(description="Final response to the user. This will be shown to the user after the conversation ends.")

class Handoff(BaseModel):
    """Action to handoff the conversation to another agent."""
    
    destination: str = Field(description="The name of the agent to handoff the conversation to.")

    message: str = Field(description="Message to the agent to handoff the conversation. Question or answer depending on interaction")

class Action(BaseModel):
    """Action to perform."""

    comment: Optional[str] = Field(None, description="Comment to the user, if it need. Can be shown to user between agent interactions.")
    
    action: Union[EndConversation, Handoff] = Field(
        description="Action to perform. If you want to respond to user, use EndConversation. "
        "If you need to transfer the conversation to another agent, use Handoff."
    )
    

def create_agent_node(
    name: str,
    make_prompt: Optional[Callable] = None,
    end_destination: str = "END",
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
        make_prompt: Optional prompt function for the agent
        end_destination: Name of the destination if the conversation is finished
        
    Returns:
        A tuple containing the agent and the node function
    """
    
    # Define the node function that wraps the agent
    # We use Command[Any] to indicate it can go to any destination
    async def agent_node(state: State, config: RunnableConfig) -> Command[Any]:
        configuration = Configuration.from_runnable_config(config)
        # Initialize the model with structured output
        model = load_chat_model(configuration.model).with_structured_output(Action)

        # Invoke the agent with the current state
        messages = make_prompt(state, config)

        print_messages(messages)
        output = await model.ainvoke(messages, config)
        print('output', output)

        if isinstance(output.action, EndConversation):
            # Return the command with the updated state and finish destination
            return Command(
                update={
                    # Share the agent's message history with other agents and user
                    "messages": [ai_message(name=name, content=output.action.response)],
                },
                goto=end_destination,
            )
        

        if isinstance(output.action, Handoff):
            response_messages = [ai_message(name=name, content=output.comment)] if output.comment else []
            
            response_messages = response_messages + [
                ai_message(name=name, content=output.action.message, destination=output.action.destination),
                # Add system message as last message after assistent
                # This ensures compatibility with providers that don't allow AI messages
                # at the last position of the input messages list
                SystemMessage(content=f"Agent {name} finished their turn")
            ]

            return Command(
                update={"messages": response_messages},
                goto=output.action.destination,
            )
    
    # Return both the agent and the node function
    return agent_node 


def ai_message(name: str, content: str, destination: Optional[str] = 'User') -> AIMessage:
    """Create an AIMessage with the given name and content. If destination is provided, add it to the message."""
    return AIMessage(
        name=name, # Name supported not by all providers, will add it to the message
        content=f"{name} to {destination}: {content}"
    )

def print_messages(messages: list[BaseMessage]):
    print('messages')
    for message in messages:
        print(message.pretty_print())

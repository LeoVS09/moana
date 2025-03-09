"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import MessagesState, add_messages
from typing_extensions import Annotated


@dataclass
class State(MessagesState):
    """Represents the state of the agent, extending MessagesState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """
    
    memories: str = field(default="")
    """
    String containing the agent's memories retrieved from the memory store.
    
    This field stores relevant context from past conversations that can be
    used to inform the agent's responses in the current conversation.
    """ 
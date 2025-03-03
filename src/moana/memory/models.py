"""Memory data models."""

from typing import List
from pydantic import BaseModel, Field

# Contextual memory
class Memory(BaseModel):
    """Save notable memories the user has shared with you for later recall."""

    content: str = Field(
        ..., 
        description="The main content of the memory."
        "The specific information, preference, or event being remembered."
        "For example: 'User expressed interest in learning about French.'"
    )
    context: str = Field(
        ..., 
        description="Additional context for the memory."
        "The situation or circumstance where this memory may be relevant. "
        "Include any caveats or conditions that contextualize the memory. "
        "For example, if a user shares a preference, note if it only applies "
        "in certain situations (e.g., 'only at work'). Add any other relevant "
        "'meta' details that help fully understand when and how to use this memory."
        "For example: 'This was mentioned while discussing career options in Europe.'"
    )
    confidence: str = Field(
        ..., 
        description="The confidence in memory accuracy."
        "For example: 'high', 'medium', 'low'"
    ) 

# Semantic memory
class Triple(BaseModel):
    """Store all new facts, preferences, and relationships as triples."""
    subject: str = Field(
        ..., 
        description="The subject of the triple."
    )
    predicate: str = Field(
        ..., 
        description="The predicate of the triple."
    )
    object: str = Field(
        ..., 
        description="The object of the triple."
    )

# Semantic profile memory
# Available during every interaction
class Profile(BaseModel):
    """Represents the full representation of a user."""
    name: str | None = Field(
        None,
        description="The name of the user."
    )
    age: int | None = Field(
        None,
        description="The age of the user."
    )
    gender: str | None = Field(
        None,
        description="The gender of the user."
    )
    location: str | None = Field(
        None,
        description="The location of the user."
    )

# Episodic memory
class Episode(BaseModel):  # 
    """
    Write the episode from the perspective of the agent within it. 
    Use the benefit of hindsight to record the memory, 
    saving the agent's key internal thought process so it can learn over time.
    """

    observation: str = Field(..., description="The context and setup - what happened")
    thoughts: str = Field(
        ...,
        description="Internal reasoning process and observations of the agent"
        "in the episode that let it arrive at the correct action and result. 'I ...'",
    )
    action: str = Field(
        ...,
        description="What was done, how, and in what format."
        "(Include whatever is salient to the success of the action). I ..",
    )
    result: str = Field(
        ...,
        description="Outcome and retrospective. What did you do well?"
        "What could you do better next time? I ...",
    )

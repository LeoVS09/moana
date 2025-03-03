"""Memory data models."""

from pydantic import BaseModel, Field

class Memory(BaseModel):
    """
    Save notable memories the user has shared with you for later recall. 
    Memories about new facts, preferences, and relationships.
    """

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
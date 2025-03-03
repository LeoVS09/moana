"""Memory data models."""

from pydantic import BaseModel, Field

class Memory(BaseModel):
    """Memories about new facts, preferences, and relationships."""
    content: str = Field(..., description="The main content of the memory. For example:'User expressed interest in learning about French.'")
    context: str = Field(..., description="Additional context for the memory. For example:'This was mentioned while discussing career options in Europe.'")
    confidence: str = Field(..., description="The confidence in memory accuracy. For example: 'high', 'medium', 'low'") 
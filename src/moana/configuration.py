"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import os
from typing import Annotated, Optional, Any

from langchain_core.runnables import RunnableConfig, ensure_config

from moana import prompts

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent.
    
    This class can be configured through environment variables or via the configurable
    parameter in RunnableConfig. Environment variables take precedence over configurable values.
    
    Example:
        ```
        # .env file
        USER_ID=user123
        MODEL=anthropic/claude-3-5-sonnet-20240620
        MAX_SEARCH_RESULTS=5
        ```
    """

    """Can be set with USER_ID environment variable."""
    user_id: str = field(
        default="default",
        metadata={
            "description": "The ID of the user to remember in the conversation. "
        },
    )

    """Can be set with SYSTEM_PROMPT environment variable."""
    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent. "
        },
    )

    """Can be set with MODEL environment variable.""" 
    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="anthropic/claude-3-5-sonnet-20240620",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name. "
        },
    )

    """Can be set with MAX_SEARCH_RESULTS environment variable."""
    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query. "            
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        
        # Get field names that can be initialized
        _fields = {f.name for f in fields(cls) if f.init}
        
        # Combine environment variables and configurable values
        values: dict[str, Any] = {
            f_name: os.environ.get(f_name.upper(), configurable.get(f_name))
            for f_name in _fields
        }
        
        # Use default values when neither env var nor configurable is set
        return cls(**{k: v for k, v in values.items() if v is not None})

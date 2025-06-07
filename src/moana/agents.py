import os
from typing import List, Dict, Optional
from praisonaiagents import Agent

from configuration import config, AgentConfig
from tools import get_tools_from_names


MODEL = os.getenv("MODEL")
print('AGENTS MODEL:', MODEL)


def create_agent_from_config(agent_config: AgentConfig, model: str) -> Agent:
    """Create an Agent instance from configuration with early return validation."""
    if not agent_config.name:
        raise ValueError("Agent configuration must include a name")
    
    # Handle special fields
    tools = get_tools_from_names(agent_config.tools)
    
    # Get all config as dict and extract special fields
    config_dict = agent_config.model_dump()
    config_dict.pop('tools', None)  # Remove tools as we handle it specially
    
    # Add our processed special fields
    config_dict['llm'] = model
    config_dict['tools'] = tools

    agent = Agent(**config_dict)
    print('AGENT:', agent.name)
    
    return agent


def build_agents_list(model: str) -> List[Agent]:
    """Build agents list from configuration with early return on errors."""
    try:
        if not config.agents:
            return []
        
        return [create_agent_from_config(agent_config, model) for agent_config in config.agents]
    
    except Exception as e:
        print(f"Error loading agents configuration: {e}")
        return []


def build_agents_dict(agents: List[Agent]) -> Dict[str, Agent]:
    """Build agents dictionary from agents list for easy lookup by name."""
    if not agents:
        return {}
    
    return {agent.name: agent for agent in agents}

def get_agents():
    # Build agents list and dictionary dynamically from configuration
    agents_list = build_agents_list(MODEL)
    agents_dict = build_agents_dict(agents_list)
    print('AGENTS DICT:', agents_dict)

    def get_agent(name: str, raise_error: bool = True) -> Optional[Agent]:
        """Get agent by name with optional error handling.
        
        Args:
            name: Agent name to lookup
            raise_error: If True, raises ValueError when agent not found. 
                        If False, returns None when agent not found.
        
        Returns:
            Agent instance or None (when raise_error=False and agent not found)
            
        Raises:
            ValueError: When agent not found and raise_error=True
        """
        if name not in agents_dict:
            if raise_error:
                available_agents = ", ".join(agents_dict.keys()) if agents_dict else "No agents configured"
                raise ValueError(f"Agent '{name}' not found. Available agents: {available_agents}")
            return None
        
        return agents_dict[name]

    return agents_list, agents_dict, get_agent




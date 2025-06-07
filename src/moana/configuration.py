import yaml
from typing import List
from pydantic import BaseModel, ConfigDict


class AgentConfig(BaseModel):
    """Flexible agent configuration that accepts any Agent properties."""
    model_config = ConfigDict(extra='allow')
    
    # Required field
    name: str
    
    # Optional tools list (handled specially)
    tools: List[str] = []


class Configuration(BaseModel):
    """Application configuration with manual YAML loading."""
    
    agents: List[AgentConfig] = []


def load_configuration() -> Configuration:
    """Load and return the configuration object."""
    try:
        with open("configuration.yaml", "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            return Configuration(**yaml_data if yaml_data else {})
    except FileNotFoundError:
        # Return default configuration if file doesn't exist
        return Configuration()
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}") 
    

config = load_configuration()
print('CONFIG:', config)
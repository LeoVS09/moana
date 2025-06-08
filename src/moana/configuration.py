import yaml
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from pprint import pprint


class AgentConfig(BaseModel):
    """Flexible agent configuration that accepts any Agent properties."""
    model_config = ConfigDict(extra='allow')
    
    # Required field
    name: str
    
    # Optional tools list (handled specially)
    tools: List[str] = []


class TaskConfig(BaseModel):
    """Flexible task configuration that accepts any Task properties."""
    model_config = ConfigDict(extra='allow')
    
    # Required fields
    name: str
    description: str
    expected_output: str
    agent: str  # Agent name reference

class PraisonConfig(BaseModel):
    """Praison configuration with manual YAML loading."""
    model_config = ConfigDict(extra='allow')
    
    process: str = "sequential"

class MessageConfig(BaseModel):
    """User message configuration."""
    model_config = ConfigDict(extra='allow')
    
    content: Optional[str | object] = None

class Configuration(BaseModel):
    """Application configuration with manual YAML loading."""
    
    praison: PraisonConfig = PraisonConfig()
    agents: List[AgentConfig] = []
    tasks: List[TaskConfig] = []
    message: Optional[MessageConfig] = MessageConfig()


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
pprint(config.model_dump(), width=80, depth=10)
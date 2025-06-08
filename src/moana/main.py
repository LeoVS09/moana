import os
from praisonaiagents import PraisonAIAgents
from agents import get_agents
from tasks import build_tasks
from configuration import config
from dataclasses import dataclass

MODEL = os.getenv("MODEL")
MANAGER_MODEL = os.getenv("MANAGER_MODEL", MODEL)
print('MANAGER MODEL:', MANAGER_MODEL)




@dataclass
class RawResult:
    raw: str

@dataclass
class ContentToContext:
    name: str = "User Input"
    result: RawResult = None
    
    def __init__(self, content: str):
        self.name = "User Input"
        self.result = RawResult(content)

def main():
    agents_list, agents_dict, get_agent = get_agents()
    tasks_list, tasks_dict = build_tasks(config.message, config.tasks, get_agent)

    # Run with hierarchical process
    agents = PraisonAIAgents(
        agents=agents_list,
        tasks=tasks_list,
        manager_llm=MANAGER_MODEL,
        **config.praison.model_dump()
    )

    result = agents.start() # Start.content not working with workflow
    print('RESULT:', result)
import os
from praisonaiagents import PraisonAIAgents
from agents import get_agents
from tasks import get_tasks
from configuration import config

MODEL = os.getenv("MODEL")
MANAGER_MODEL = os.getenv("MANAGER_MODEL", MODEL)
print('MANAGER MODEL:', MANAGER_MODEL)

def main():
    agents_list, agents_dict, get_agent = get_agents()
    tasks_list, tasks_dict, get_task = get_tasks(get_agent)

    # Run with hierarchical process
    agents = PraisonAIAgents(
        agents=agents_list,
        tasks=tasks_list,
        manager_llm=MANAGER_MODEL,
        **config.praison.model_dump()
    )

    start_config = config.start.model_dump()
    print('START CONFIG:', start_config)
    result = agents.start(**start_config)
    print('RESULT:', result)
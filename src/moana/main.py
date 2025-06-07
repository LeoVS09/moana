import os
from praisonaiagents import PraisonAIAgents
from agents import get_agents
from tasks import get_tasks

MODEL = os.getenv("MODEL")
MANAGER_MODEL = os.getenv("MANAGER_MODEL", MODEL)
print('MANAGER MODEL:', MANAGER_MODEL)

def main():
    agents_list, agents_dict, get_agent = get_agents()
    tasks_list = get_tasks(get_agent)

    # Run with hierarchical process
    agents = PraisonAIAgents(
        agents=agents_list,
        tasks=tasks_list,
        verbose=False,
        process="hierarchical",
        manager_llm=MANAGER_MODEL
    )

    result = agents.start()
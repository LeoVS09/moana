import os
from praisonaiagents import PraisonAIAgents
from agents import researcher, writer
from tasks import task1, task2

MODEL = os.getenv("MODEL")
MANAGER_MODEL = os.getenv("MANAGER_MODEL", MODEL)
print('MANAGER MODEL:', MANAGER_MODEL)

def main():
    # Run with hierarchical process
    agents = PraisonAIAgents(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=False,
        process="hierarchical",
        manager_llm=MANAGER_MODEL
    )

    result = agents.start()
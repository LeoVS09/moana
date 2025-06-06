import os
from praisonaiagents import Agent, Task, PraisonAIAgents

from tools import internet_search_tool


MODEL = os.getenv("MODEL")
print('MODEL', MODEL)

# Create multiple agents
researcher = Agent(
    name="Researcher",
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments in AI",
    backstory="You are an expert at a technology research group",
    verbose=True,
    llm=MODEL,
    markdown=True,
    tools=[internet_search_tool]
)

writer = Agent(
    name="Writer",
    role="Tech Content Strategist",
    goal="Craft compelling content on tech advancements",
    backstory="You are a content strategist",
    llm=MODEL,
    markdown=True
)

# Define multiple tasks
task1 = Task(
    name="research_task",
    description="Analyze 2024's AI advancements",
    expected_output="A detailed report",
    agent=researcher
)

task2 = Task(
    name="writing_task",
    description="Create a blog post about AI advancements",
    expected_output="A blog post",
    agent=writer
)

def run_agents():
    # Run with hierarchical process
    agents = PraisonAIAgents(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=False,
        process="hierarchical",
        manager_llm=MODEL
    )

    result = agents.start()
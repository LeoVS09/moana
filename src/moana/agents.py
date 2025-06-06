import os
from praisonaiagents import Agent

from tools import internet_search_tool


MODEL = os.getenv("MODEL")
print('AGENTS MODEL:', MODEL)

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


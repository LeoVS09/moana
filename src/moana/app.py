import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
from praisonaiagents import Agent, Task, PraisonAIAgents



MODEL = os.getenv("MODEL")
print('MODEL', MODEL)

# Create agents with specific roles
diet_agent = Agent(
    instructions="Give me 5 healthy food recipes",
    llm=MODEL,
)

blog_agent = Agent(
    instructions="Write a blog post about the food recipes",
    llm=MODEL,
)

# Run multiple agents
agents = PraisonAIAgents(agents=[diet_agent, blog_agent])
agents.start()
from praisonaiagents import Task
from agents import researcher, writer

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


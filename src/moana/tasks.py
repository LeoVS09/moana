from praisonaiagents import Task

def get_tasks(get_agent):
    task1 = Task(
        name="research_task",
        description="Analyze 2024's AI advancements",
        expected_output="A detailed report",
        agent=get_agent("Researcher")
    )

    task2 = Task(
        name="writing_task",
        description="Create a blog post about AI advancements",
        expected_output="A blog post",
        agent=get_agent("Writer")
    )

    return [task1, task2]

from typing import List, Dict, Optional, Tuple
from praisonaiagents import Task

from configuration import TaskConfig, MessageConfig


def build_tasks(message: MessageConfig, tasks_config: List[TaskConfig], get_agent) -> Tuple[List[Task], Dict[str, Task]]:
    """Build tasks."""
    tasks_list = []
    tasks_dict = {}

    for task_config in tasks_config:
        if not task_config.name:
            raise ValueError("Task configuration must include a name")
        
        if not task_config.agent:
            raise ValueError(f"Task '{task_config.name}' must reference an agent")
        
        # Get all config as dict and extract special fields
        config_dict = task_config.model_dump()

        # Get agent instance
        agent = get_agent(task_config.agent)
        # Add our processed special fields
        config_dict['agent'] = agent

        context_names = config_dict.pop('context', [])
        # TODO: modify context after task creation to resolvecurcular dependencies
        # example https://github.com/MervinPraison/PraisonAI/blob/main/src/praisonai/praisonai/agents_generator.py#L620
        if len(context_names) > 0:
            context = [tasks_dict[name] for name in context_names]
            config_dict['context'] = context

        if message and message.content:
            config_dict['description'] = config_dict['description'] + "\nUser Message: " + message.content

        task = Task(**config_dict)
        print('TASK:', task.name, task.context)

        tasks_list.append(task)
        tasks_dict[task.name] = task

    return tasks_list, tasks_dict

from typing import List, Dict, Optional, Tuple
from praisonaiagents import Task

from configuration import TaskConfig


def build_tasks(tasks_config: List[TaskConfig], get_agent) -> Tuple[List[Task], Dict[str, Task]]:
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
        if len(context_names) > 0:
            context = [tasks_dict[name] for name in context_names]
            config_dict['context'] = context

        task = Task(**config_dict)
        print('TASK:', task.name, task.context)

        tasks_list.append(task)
        tasks_dict[task.name] = task

    return tasks_list, tasks_dict

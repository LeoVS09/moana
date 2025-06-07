from typing import List, Dict, Optional
from praisonaiagents import Task

from configuration import config, TaskConfig


def create_task_from_config(task_config: TaskConfig, get_agent) -> Task:
    """Create a Task instance from configuration with early return validation."""
    if not task_config.name:
        raise ValueError("Task configuration must include a name")
    
    if not task_config.agent:
        raise ValueError(f"Task '{task_config.name}' must reference an agent")
    
    # Get agent instance
    agent = get_agent(task_config.agent)
    
    # Get all config as dict and extract special fields
    config_dict = task_config.model_dump()
    config_dict.pop('agent', None)  # Remove agent as we handle it specially
    
    # Add our processed special fields
    config_dict['agent'] = agent

    task = Task(**config_dict)
    print('TASK:', task.name)
    
    return task


def build_tasks_list(get_agent) -> List[Task]:
    """Build tasks list from configuration with early return on errors."""
    try:
        if not config.tasks:
            return []
        
        return [create_task_from_config(task_config, get_agent) for task_config in config.tasks]
    
    except Exception as e:
        print(f"Error loading tasks configuration: {e}")
        return []


def build_tasks_dict(tasks: List[Task]) -> Dict[str, Task]:
    """Build tasks dictionary from tasks list for easy lookup by name."""
    if not tasks:
        return {}
    
    return {task.name: task for task in tasks}


def get_tasks(get_agent):
    """Get tasks built from configuration."""
    # Build tasks list and dictionary dynamically from configuration
    tasks_list = build_tasks_list(get_agent)
    tasks_dict = build_tasks_dict(tasks_list)
    print('TASKS DICT:', tasks_dict)

    def get_task(name: str, raise_error: bool = True) -> Optional[Task]:
        """Get task by name with optional error handling.
        
        Args:
            name: Task name to lookup
            raise_error: If True, raises ValueError when task not found. 
                        If False, returns None when task not found.
        
        Returns:
            Task instance or None (when raise_error=False and task not found)
            
        Raises:
            ValueError: When task not found and raise_error=True
        """
        if name not in tasks_dict:
            if raise_error:
                available_tasks = ", ".join(tasks_dict.keys()) if tasks_dict else "No tasks configured"
                raise ValueError(f"Task '{name}' not found. Available tasks: {available_tasks}")
            return None
        
        return tasks_dict[name]

    return tasks_list, tasks_dict, get_task

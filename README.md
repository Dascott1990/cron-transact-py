<div align="center">

# Dascott Task Manager: Reliable & Efficient Workflow Automation

#### [Documentation](#) &nbsp;&nbsp;•&nbsp;&nbsp; [Examples](#) &nbsp;&nbsp;•&nbsp;&nbsp; [GitHub](#) &nbsp;&nbsp;•&nbsp;&nbsp; [Community](#)
</div>

---

Dascott Task Manager is a **lightweight, self-sufficient task automation system** designed for seamless execution and recovery of critical workflows.

### Key Features:

- Automate scheduled jobs with zero manual intervention.
- Ensure **fault-tolerant execution** for critical workflows.
- Manage distributed, long-running tasks with **automatic recovery**.
- Simple, self-contained, and **easy to integrate**.

## Example Usage

```python
@task_manager.task()
def job_one():
    ...

@task_manager.task()
def job_two():
    ...

@task_manager.workflow()
def automated_process():
    job_one()
    job_two()
```

If interrupted, tasks **resume automatically** from the last successful step.

## Getting Started

Install and configure:

```shell
python3 -m venv dascott-env
cd dascott-env
source .venv/bin/activate
pip install dascott-manager
task-manager init --config
```

Run a simple workflow:

```python
from fastapi import FastAPI
from dascott_manager import TaskManager

app = FastAPI()
task_manager = TaskManager(fastapi=app)

@task_manager.task()
def morning_routine():
    print("Morning routine executed!")

@task_manager.task()
def night_routine():
    print("Night routine executed!")

@task_manager.workflow()
def daily_tasks():
    morning_routine()
    task_manager.sleep(3600)
    night_routine()

@app.get("/")
def trigger():
    daily_tasks()
```

Save as `main.py` and start it. Visit `localhost:8000` to initiate the workflow. If interrupted, restart and it **resumes automatically**.

## Documentation

[Read More](#)

## Examples

- **Automated Reports** &mdash; Generate and send reports daily.
- **Recurring Alerts** &mdash; Schedule notifications and reminders.
- **Database Maintenance** &mdash; Periodically clean or sync data sources.

## Community

Join discussions, contribute, or report issues on [GitHub](#) and [Community](#).

---

Built by Dascott for **efficiency, automation, and reliability** in task execution.


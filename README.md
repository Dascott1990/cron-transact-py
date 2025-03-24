<div align="center">

# Task Scheduler: A Lightweight, Reliable Execution System

#### [Documentation](#) &nbsp;&nbsp;•&nbsp;&nbsp; [Twitter](#) &nbsp;&nbsp;•&nbsp;&nbsp; [GitHub](#) &nbsp;&nbsp;•&nbsp;&nbsp; [Community](#)
</div>

---

This Task Scheduler is a robust system for **automating and managing scheduled tasks**.

For example:

```python
@scheduler.task()
def job_one():
    ...

@scheduler.task()
def job_two():
    ...

@scheduler.workflow()
def daily_routine():
    job_one()
    job_two()
```

This ensures tasks are **resilient and automatically recover** if interrupted or fail. Perfect for:

- Running scheduled jobs without manual intervention.
- Automating background tasks and workflows.
- Ensuring fault-tolerant execution of critical processes.
- Managing distributed or long-running tasks efficiently.

Unlike bulky third-party services, this system is **lightweight, self-contained, and works out-of-the-box** with minimal setup.

## Getting Started

Install and configure:

```shell
python3 -m venv scheduler-env
cd scheduler-env
source .venv/bin/activate
pip install task-scheduler
scheduler init --config
```

Example usage:

```python
from fastapi import FastAPI
from task_scheduler import Scheduler

app = FastAPI()
scheduler = Scheduler(fastapi=app)

@scheduler.task()
def morning_task():
    print("Morning task executed!")

@scheduler.task()
def evening_task():
    print("Evening task executed!")

@scheduler.workflow()
def daily_routine():
    morning_task()
    scheduler.sleep(3600)
    evening_task()

@app.get("/")
def trigger():
    daily_routine()
```

Save as `main.py` and run it. Access `localhost:8000` to start the scheduler. If interrupted, restart and it will **resume** from where it left off.

## Documentation

[Read More](#)

## Examples

- **Automated Reports** &mdash; Generate and send reports daily.
- **Recurring Notifications** &mdash; Schedule messages or reminders.
- **Data Sync & Cleanup** &mdash; Periodically clean databases or sync data sources.

## Community

Join the discussion, contribute, or report issues on [GitHub](#) and [Community](#).

---

Ensuring **efficiency, resilience, and automation** for your scheduled tasks.


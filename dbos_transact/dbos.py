import uuid
from functools import wraps
from typing import Any, Callable, Optional, Protocol, TypeVar, cast

import dbos_transact.utils as utils
from dbos_transact.workflows import WorkflowContext

from .application_database import ApplicationDatabase
from .dbos_config import ConfigFile, load_config
from .logger import config_logger, dbos_logger
from .system_database import (
    SystemDatabase,
    WorkflowInputs,
    WorkflowStatusInternal,
    WorkflowStatusString,
)


class WorkflowProtocol(Protocol):
    __qualname__: str

    def __call__(self, ctx: WorkflowContext, *args: Any, **kwargs: Any) -> Any: ...


Workflow = TypeVar("Workflow", bound=WorkflowProtocol)


class DBOS:
    def __init__(self, config: Optional[ConfigFile] = None) -> None:
        if config is None:
            config = load_config()
        config_logger(config)
        dbos_logger.info("Initializing DBOS!")
        self.config = config
        self.sys_db = SystemDatabase(config)
        self.app_db = ApplicationDatabase(config)

    def destroy(self) -> None:
        self.sys_db.destroy()
        self.app_db.destroy()

    def workflow(self) -> Callable[[Workflow], Workflow]:
        def decorator(func: Workflow) -> Workflow:
            @wraps(func)
            def wrapper(_: WorkflowContext, *args: Any, **kwargs: Any) -> Any:
                workflow_uuid = str(uuid.uuid4())

                status: WorkflowStatusInternal = {
                    "workflow_uuid": workflow_uuid,
                    "status": WorkflowStatusString.PENDING.value,
                    "name": func.__qualname__,
                    "output": None,
                    "error": None,
                }
                self.sys_db.update_workflow_status(status)

                inputs: WorkflowInputs = {
                    "args": args,
                    "kwargs": kwargs,
                }
                self.sys_db.update_workflow_inputs(
                    workflow_uuid, utils.serialize(inputs)
                )

                ctx = WorkflowContext(workflow_uuid, self.sys_db)

                try:
                    output = func(ctx, *args, **kwargs)
                except Exception as error:
                    status["status"] = WorkflowStatusString.ERROR.value
                    status["error"] = utils.serialize(error)
                    self.sys_db.update_workflow_status(status)
                    raise error

                status["status"] = WorkflowStatusString.SUCCESS.value
                status["output"] = utils.serialize(output)
                self.sys_db.update_workflow_status(status)
                return output

            return cast(Workflow, wrapper)

        return decorator

    def wf_ctx(self) -> WorkflowContext:
        return cast(WorkflowContext, None)

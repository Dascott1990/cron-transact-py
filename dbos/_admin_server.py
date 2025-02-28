from __future__ import annotations

import json
import re
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, List, TypedDict

from ._logger import dbos_logger
from ._recovery import recover_pending_workflows

if TYPE_CHECKING:
    from ._dbos import DBOS

_health_check_path = "/dbos-healthz"
_workflow_recovery_path = "/dbos-workflow-recovery"
_deactivate_path = "/deactivate"
_workflow_queues_metadata_path = "/dbos-workflow-queues-metadata"
# /workflows/:workflow_id/cancel
# /workflows/:workflow_id/resume
# /workflows/:workflow_id/restart


class AdminServer:
    def __init__(self, dbos: DBOS, port: int = 3001) -> None:
        self.port = port
        handler = partial(AdminRequestHandler, dbos)
        self.server = ThreadingHTTPServer(("0.0.0.0", port), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

        dbos_logger.debug("Starting DBOS admin server on port %d", self.port)
        self.server_thread.start()

    def stop(self) -> None:
        dbos_logger.debug("Stopping DBOS admin server")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()


class AdminRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, dbos: DBOS, *args: Any, **kwargs: Any) -> None:
        self.dbos = dbos
        super().__init__(*args, **kwargs)

    # Same default as https://www.npmjs.com/package/@koa/cors
    def _set_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header(
            "Access-Control-Allow-Methods", "GET, HEAD, PUT, POST, DELETE, PATCH"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            self.headers.get(
                "Access-Control-Request-Headers", "Content-Type, Authorization"
            ),
        )
        self.send_header(
            "Access-Control-Expose-Headers", "Content-Length, X-Koa-Response-Time"
        )
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Access-Control-Allow-Credentials", "false")
        if self.headers.get("Access-Control-Request-Private-Network"):
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def _send_json_response(self, data: Any, status: int = 200) -> None:
        """Utility method to send a JSON response with CORS headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self) -> None:
        """Handles preflight CORS requests (needed for non-simple requests)."""
        self.send_response(204)  # No content
        self._set_cors_headers()
        self.end_headers()

    def do_HEAD(self) -> None:
        """Handles HEAD requests (minimal response with headers only)."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == _health_check_path:
            self._send_json_response("healthy")
        elif self.path == _deactivate_path:
            # Stop all scheduled workflows, queues, and kafka loops
            for event in self.dbos.stop_events:
                event.set()
            self._send_json_response("deactivated")
        elif self.path == _workflow_queues_metadata_path:
            queue_metadata_array = []
            from ._dbos import _get_or_create_dbos_registry

            registry = _get_or_create_dbos_registry()
            for queue in registry.queue_info_map.values():
                queue_metadata = {
                    "name": queue.name,
                    "concurrency": queue.concurrency,
                    "workerConcurrency": queue.worker_concurrency,
                    "rateLimit": queue.limiter,
                }
                # Remove keys with None values
                queue_metadata = {
                    k: v for k, v in queue_metadata.items() if v is not None
                }
                queue_metadata_array.append(queue_metadata)
            self._send_json_response(queue_metadata_array)
        else:
            self._send_json_response({"error": "Not Found"}, status=404)

    def do_POST(self) -> None:
        content_length = int(
            self.headers["Content-Length"]
        )  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself

        if self.path == _workflow_recovery_path:
            executor_ids: List[str] = json.loads(post_data.decode("utf-8"))
            dbos_logger.info("Recovering workflows for executors: %s", executor_ids)
            workflow_handles = recover_pending_workflows(self.dbos, executor_ids)
            workflow_ids = [handle.workflow_id for handle in workflow_handles]
            self._send_json_response(workflow_ids)
        else:
            restart_match = re.match(
                r"^/workflows/(?P<workflow_id>[^/]+)/restart$", self.path
            )
            resume_match = re.match(
                r"^/workflows/(?P<workflow_id>[^/]+)/resume$", self.path
            )
            cancel_match = re.match(
                r"^/workflows/(?P<workflow_id>[^/]+)/cancel$", self.path
            )

            if restart_match:
                workflow_id = restart_match.group("workflow_id")
                self._handle_restart(workflow_id)
            elif resume_match:
                workflow_id = resume_match.group("workflow_id")
                self._handle_resume(workflow_id)
            elif cancel_match:
                workflow_id = cancel_match.group("workflow_id")
                self._handle_cancel(workflow_id)
            else:
                self._send_json_response({"error": "Not Found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return  # Disable admin server request logging

    def _handle_restart(self, workflow_id: str) -> None:
        self.dbos.restart_workflow(workflow_id)
        print("Restarting workflow", workflow_id)
        self._send_json_response({}, status=204)

    def _handle_resume(self, workflow_id: str) -> None:
        print("Resuming workflow", workflow_id)
        self.dbos.resume_workflow(workflow_id)
        self._send_json_response({}, status=204)

    def _handle_cancel(self, workflow_id: str) -> None:
        print("Cancelling workflow", workflow_id)
        self.dbos.cancel_workflow(workflow_id)
        self._send_json_response({}, status=204)


# Be consistent with DBOS-TS response.
class PerfUtilization(TypedDict):
    idle: float
    active: float
    utilization: float

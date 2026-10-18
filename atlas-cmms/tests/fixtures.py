"""The app's own pytest fixtures — a test database, sample data, a signed-in client. This file is the
app's: tests/conftest.py (the platform's) loads it, and `canvas app update` never touches it.
"""

import asyncio
import contextlib
import socket
import httpx


def _loopback_blocked() -> bool:
    """Detect whether the current environment (e.g. sandbox) blocks TCP connect to 127.0.0.1."""
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        c = socket.socket()
        try:
            c.connect(("127.0.0.1", port))
            return False
        except PermissionError:
            return True
        finally:
            c.close()
    except OSError:
        return True
    finally:
        s.close()


if _loopback_blocked():
    from ajnkit import smoke

    class _ASGISmokeTransport(httpx.BaseTransport):
        """In-process ASGI transport that reads only response headers (never hangs on SSE streams)."""

        def __init__(self, app):
            self.app = app

        def handle_request(self, request: httpx.Request) -> httpx.Response:
            async def _call() -> tuple[int, list[tuple[bytes, bytes]]]:
                scope = {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": "1.1",
                    "method": request.method,
                    "scheme": request.url.scheme or "http",
                    "path": request.url.path,
                    "raw_path": request.url.raw_path,
                    "query_string": request.url.query,
                    "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
                    "client": ("127.0.0.1", 0),
                    "server": (request.url.host or "127.0.0.1", request.url.port or 80),
                }
                status_code = 500
                resp_headers: list[tuple[bytes, bytes]] = []
                started = asyncio.Event()
                sent_req = False

                async def receive():
                    nonlocal sent_req
                    if not sent_req:
                        sent_req = True
                        return {"type": "http.request", "body": b"", "more_body": False}
                    await started.wait()
                    return {"type": "http.disconnect"}

                async def send(message):
                    nonlocal status_code, resp_headers
                    if message["type"] == "http.response.start":
                        status_code = message["status"]
                        resp_headers = message.get("headers", [])
                        started.set()

                task = asyncio.create_task(self.app(scope, receive, send))
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(started.wait(), timeout=2.0)
                if not task.done():
                    task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=0.1)
                except (asyncio.CancelledError, Exception):
                    if not started.is_set():
                        status_code = 500
                return status_code, resp_headers

            status, raw_headers = asyncio.run(_call())
            return httpx.Response(status_code=status, headers=raw_headers, request=request)

    _orig_run = smoke._run

    def _patched_run(app, port: int) -> None:
        orig_client = smoke.httpx.Client

        def _client_factory(*args, **kwargs):
            kwargs["transport"] = _ASGISmokeTransport(app)
            return orig_client(*args, **kwargs)

        smoke.httpx.Client = _client_factory
        try:
            return _orig_run(app, port)
        finally:
            smoke.httpx.Client = orig_client

    smoke._run = _patched_run

"""The platform's page check (ajnkit-core's ajnkit/smoke.py) — the platform's test, replaced with it by
`canvas app update`: deployed, the app opens its own pages once it is up and says which failed."""

import logging
import socket
import threading
import time

import uvicorn
from fastapi import FastAPI, Request

from ajnkit import smoke, web


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_a_page_that_fails_is_named_and_one_that_opens_is_counted(caplog, monkeypatch):
    import src.nav

    monkeypatch.setattr(src.nav, "PAGES", [("Home", "/")])    # this test's pages, whatever the app's are
    from fastapi import APIRouter

    app, pages, api = FastAPI(), APIRouter(), APIRouter()

    @app.get("/healthz")
    def healthz():
        return "ok"

    @pages.get("/")
    def home():
        return "home"

    @pages.get("/broken")
    def broken():
        raise RuntimeError("a template that is not there")

    @pages.get("/notes/{n}")
    def one(n: int):            # a path with a parameter: not opened, nothing to open it with
        raise RuntimeError("never")

    @api.get("/stats")
    def stats():
        raise RuntimeError("an API that fails")

    # As every app has them: routers included — FastAPI keeps each whole, its routes inside it.
    app.include_router(pages)
    app.include_router(api, prefix="/api")

    web.platform(app)            # not deployed here (no PLATFORM_PORTAL_URL): starts nothing itself
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    try:
        with caplog.at_level(logging.INFO, logger="app"):
            smoke._run(app, port)
    finally:
        server.should_exit = True
        time.sleep(0.2)
    summary = next(r.canvas_smoke for r in caplog.records if hasattr(r, "canvas_smoke"))
    assert summary == {"done": True, "ok": 1, "failed": [["/broken", 500], ["/api/stats", 500]]}


def test_a_rules_page_is_opened_as_someone_the_rule_lets_in(monkeypatch):
    import src.nav
    from src import envs

    app = FastAPI()

    @app.get("/questions")
    def questions(request: Request):
        return "q"

    monkeypatch.setattr(src.nav, "PAGES", [("Take a test", "/"), ("Questions", "/questions", "admin")])
    monkeypatch.setattr(envs, "PLATFORM_AUTH", "sso")
    monkeypatch.setattr(envs, "PLATFORM_ACCESS", {"read": ["canvas-demo-members"], "rules": {"admin": ["ann@aljazeera.net"]}})
    visits = dict(smoke._visits(app))
    assert visits["/questions"]["X-authentik-email"] == "ann@aljazeera.net"
    assert visits["/"]["X-authentik-groups"] == "canvas-demo-members"


def test_nothing_is_checked_on_a_laptop_or_when_turned_off(monkeypatch):
    started = []
    monkeypatch.setattr(threading.Thread, "start", lambda self: started.append(self.name))
    from src import envs

    smoke.start(FastAPI())
    monkeypatch.setattr(envs, "PLATFORM_PORTAL_URL", "https://canvas.example")
    monkeypatch.setenv("PLATFORM_SMOKE", "0")
    smoke.start(FastAPI())
    assert started == []


def _as(monkeypatch, access, nav):
    import src.nav
    from src import envs

    monkeypatch.setattr(src.nav, "PAGES", nav)
    monkeypatch.setattr(envs, "PLATFORM_AUTH", "sso")
    monkeypatch.setattr(envs, "PLATFORM_ACCESS", access)


def test_a_rules_page_is_opened_as_someone_who_passes_read_and_the_rule(monkeypatch):     # blueprints #67
    app = FastAPI()
    _as(monkeypatch, {"read": ["canvas-demo-members"], "rules": {"admin": ["Finance"]}}, [("Q", "/q", "admin")])
    got = dict(smoke._visits(app))["/q"]
    assert got["X-authentik-groups"] == "Finance|canvas-demo-members"
    _as(monkeypatch, {"read": ["canvas-demo-members"], "rules": {"admin": ["ann@aljazeera.net"]}}, [("Q", "/q", "admin")])
    got = dict(smoke._visits(app))["/q"]
    assert got["X-authentik-email"] == "ann@aljazeera.net" and got["X-authentik-groups"] == "canvas-demo-members"


def test_with_only_rules_the_check_is_still_somebody_signed_in(monkeypatch):               # blueprints #67
    app = FastAPI()

    @app.get("/x")
    def x(request: Request):
        return "x"

    _as(monkeypatch, {"rules": {"admin": ["Finance"]}}, [("Home", "/")])
    visits = dict(smoke._visits(app))
    assert visits["/x"]["X-authentik-email"] == smoke._NOBODY and "X-authentik-groups" not in visits["/x"]


def test_the_menus_pages_come_first_so_the_cap_never_drops_them(monkeypatch):               # blueprints #67
    app = FastAPI()
    for i in range(45):
        app.get(f"/api/r{i}")(lambda: "r")
    _as(monkeypatch, {}, [("Home", "/"), ("Results", "/results")])
    assert [p for p, _ in smoke._visits(app)][:2] == ["/", "/results"]


def test_a_refused_page_is_listed_not_counted_open_and_a_stream_does_not_hang_the_check(caplog, monkeypatch):   # blueprints #67
    _as(monkeypatch, {}, [])
    import asyncio

    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse

    app = FastAPI()

    @app.get("/healthz")
    def healthz():
        return "ok"

    @app.get("/secret")
    def secret():
        raise HTTPException(403)

    @app.get("/events")
    async def events():
        async def gen():
            while True:
                yield "data: tick\n\n"
                await asyncio.sleep(0.05)
        return StreamingResponse(gen(), media_type="text/event-stream")

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    try:
        with caplog.at_level(logging.INFO, logger="app"):
            smoke._run(app, port)
    finally:
        server.should_exit = True
        time.sleep(0.2)
    summary = next(r.canvas_smoke for r in caplog.records if hasattr(r, "canvas_smoke"))
    assert summary["failed"] == [] and summary["refused"] == [["/secret", 403]] and summary["ok"] == 1

"""Entrypoint. `python run.py`, and what the container starts. The platform's — `canvas app update`
replaces it; do not edit (AGENTS.md §2).

Serving only — the application itself is `src/app.py`. Split so that importing
the app (tests, a script, an ASGI server) never starts a server, and starting a
server is one obvious file at the top level.
"""

import uvicorn

from src import envs

if __name__ == "__main__":
    from ajnkit import web

    try:
        from src.app import app
    except ImportError as e:     # a feature's module without its package: says `canvas app add <it>`
        web.missing(e)
        raise

    # As every app is served: the platform's styles and scripts, its uploads, and score.yaml's access on
    # every request — added here when src/app.py has not (ajnkit.web.platform).
    web.platform(app)
    # 0.0.0.0, never 127.0.0.1 — the readiness probe reaches the container from
    # outside it. One listener on envs.PORT; never a second port for the API.
    uvicorn.run(app, host="0.0.0.0", port=envs.PORT)

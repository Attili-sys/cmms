"""Platform-injected environment, read in exactly one place.

Every variable here is injected by a resource declared in score.yaml. The names
are a platform contract and are IDENTICAL locally and in-cluster — never guess
one, never rename one, never read os.environ directly elsewhere.
"""

import json
import os
from pathlib import Path

# route — always present, `route` is required
PORT = int(os.environ["PORT"])
PUBLIC_URL = os.environ.get("PUBLIC_URL", f"http://localhost:{PORT}")

# The page shell's links (ajnkit.web), set by the platform: the portal, and — with
# `auth: sso` — where Sign out goes. Absent on your computer: the shell then leaves them out.
PLATFORM_PORTAL_URL = os.environ.get("PLATFORM_PORTAL_URL")
PLATFORM_SIGN_OUT_URL = os.environ.get("PLATFORM_SIGN_OUT_URL")

# "sso" or "none" — set by the platform from route.params.auth.
# It decides whether the X-authentik-* identity headers can be TRUSTED: under
# `none` there is no auth proxy in the request path, so a caller can send them
# itself. ajnkit.access and ajnkit.rbac refuse to authorise unless this is "sso".
PLATFORM_AUTH = os.environ.get("PLATFORM_AUTH", "none")

# The route's `access` in score.yaml — read/write/deny — for ajnkit.access. Set by the platform
# only when the app declares it (and only with auth: sso).
PLATFORM_ACCESS = json.loads(os.environ.get("PLATFORM_ACCESS") or "{}")

# The route's `docs` in score.yaml: "public" when the API docs skip the sign-in (ajnkit.access).
PLATFORM_DOCS = os.environ.get("PLATFORM_DOCS", "private")

# postgres — present only if score.yaml declares it. The platform hands over `postgresql://…`,
# which SQLAlchemy reads as psycopg2; this app ships psycopg 3, so name it.
DATABASE_URL = (os.environ.get("DATABASE_URL") or "").replace(
    "postgresql://", "postgresql+psycopg://", 1
) or None

# volume — the app's own disk, always mounted at /data (score.yaml sets DATA_DIR with it). On your
# computer, a `data/` folder beside the code. Build paths from it: DATA_DIR / "index.db".
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))

# llm — the gateway is OpenAI-compatible; the key is issued by the platform
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PLATFORM_LLM_MODELS = [m for m in os.environ.get("PLATFORM_LLM_MODELS", "").split(",") if m]

# email — sent by the platform for the app (ajnkit.email, which reads these itself). Cluster only:
# unset on your computer, where ajnkit.email logs the message instead.
PLATFORM_EMAIL_URL = os.environ.get("PLATFORM_EMAIL_URL")
PLATFORM_EMAIL_TOKEN = os.environ.get("PLATFORM_EMAIL_TOKEN")

# Self-hosted unrestricted edition flag (CLOUD_VERSION=false unlocks all PlanFeatures)
CLOUD_VERSION = os.environ.get("CLOUD_VERSION", "false").lower() in {"true", "1", "yes"}
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Atlas CMMS")


# secret — one variable per declared key: `envs.secret("PARTNER_API_KEY")`, where it is used. Never a
# constant here: the tests, and a pair's `canvas validate` and `canvas api pull`, import the app with
# no secret set (#110).
def secret(key: str) -> str:
    """A `secret` score.yaml declares. The platform sets it once the user has (`canvas secret set`);
    not set is an error that says so, never a quiet None. On your computer, the same name in your shell."""
    if not (value := os.environ.get(key)):
        raise RuntimeError(f"the secret {key} is not set — `canvas secret set {key}`, and declare it in score.yaml")
    return value


def secret_file(key: str) -> str:
    """A secret whose value is a file (score.yaml `files:`) — azure.json, a PEM: its contents."""
    if not (path := os.environ.get(f"{key}_FILE")):
        raise RuntimeError(f"the secret file {key} is not set — declare it under a secret's files in score.yaml")
    return Path(path).read_text()

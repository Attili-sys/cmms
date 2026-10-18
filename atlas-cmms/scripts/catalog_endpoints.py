"""Parse all 58 Spring REST controllers into fixtures/contract/endpoints.yaml."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_DIR = REPO_ROOT / "api" / "src" / "main" / "java" / "com" / "grash" / "controller"
OUTPUT_YAML = REPO_ROOT / "atlas-cmms" / "fixtures" / "contract" / "endpoints.yaml"

MAPPING_RE = re.compile(
    r"@(RequestMapping|GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\s*(?:\(([^)]*)\))?"
)
METHOD_SIG_RE = re.compile(
    r"public\s+(?:ResponseEntity<[^>]+>|[\w<>\[\],\s\?]+)\s+(\w+)\s*\(([^)]*)\)",
    re.DOTALL,
)
PRE_AUTH_RE = re.compile(r'@PreAuthorize\s*\(\s*"([^"]+)"\s*\)')


def _extract_path_and_method(annotation_name: str, args_str: str | None) -> tuple[str, str]:
    http_method = "GET"
    if annotation_name == "PostMapping":
        http_method = "POST"
    elif annotation_name == "PutMapping":
        http_method = "PUT"
    elif annotation_name == "PatchMapping":
        http_method = "PATCH"
    elif annotation_name == "DeleteMapping":
        http_method = "DELETE"
    elif annotation_name == "RequestMapping":
        http_method = "GET"
        if args_str:
            m = re.search(r"RequestMethod\.(\w+)", args_str)
            if m:
                http_method = m.group(1).upper()

    path = ""
    if args_str:
        # Look for path = "..." or value = "..." or first string literal
        m_named = re.search(r'(?:path|value)\s*=\s*"([^"]*)"', args_str)
        if m_named:
            path = m_named.group(1)
        else:
            m_str = re.search(r'"([^"]*)"', args_str)
            if m_str:
                path = m_str.group(1)
    return http_method, path


def _join_paths(prefix: str, sub: str) -> str:
    p = prefix.strip("/")
    s = sub.strip("/")
    if p and s:
        return f"/{p}/{s}"
    if p:
        return f"/{p}"
    if s:
        return f"/{s}"
    return "/"


def parse_controllers() -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    if not CONTROLLERS_DIR.exists():
        raise FileNotFoundError(f"Controllers dir not found: {CONTROLLERS_DIR}")

    for java_file in sorted(CONTROLLERS_DIR.rglob("*Controller.java")):
        content = java_file.read_text(encoding="utf-8")
        controller_name = java_file.stem

        # Find class-level @RequestMapping before 'public class'
        class_idx = content.find("public class ")
        if class_idx == -1:
            continue
        header = content[:class_idx]
        class_prefix = ""
        for m in MAPPING_RE.finditer(header):
            if m.group(1) == "RequestMapping":
                _, class_prefix = _extract_path_and_method(m.group(1), m.group(2))

        body = content[class_idx:]
        # Scan method annotations in body
        for m in MAPPING_RE.finditer(body):
            ann_name = m.group(1)
            ann_args = m.group(2)
            http_method, sub_path = _extract_path_and_method(ann_name, ann_args)
            full_path = _join_paths(class_prefix, sub_path)

            # Look around the match for @PreAuthorize and method signature
            window_before = body[max(0, m.start() - 300) : m.end()]
            window_after = body[m.end() : m.end() + 600]

            pre_auth_match = PRE_AUTH_RE.search(window_before) or PRE_AUTH_RE.search(
                window_after[:200]
            )
            auth = pre_auth_match.group(1) if pre_auth_match else "permitAll"

            sig_match = METHOD_SIG_RE.search(window_after)
            handler_name = sig_match.group(1) if sig_match else "unknown"
            params_raw = sig_match.group(2) if sig_match else ""

            path_vars = re.findall(r"@PathVariable(?:\([^)]*\))?\s+[\w<>]+\s+(\w+)", params_raw)
            req_params = re.findall(r"@RequestParam(?:\([^)]*\))?\s+[\w<>]+\s+(\w+)", params_raw)
            body_match = re.search(
                r"@RequestBody\s+([\w<>\[\]]+)\s+\w+", params_raw
            )
            request_body_type = body_match.group(1) if body_match else None

            endpoints.append(
                {
                    "controller": controller_name,
                    "handler": handler_name,
                    "method": http_method,
                    "path": full_path,
                    "auth": auth,
                    "path_variables": path_vars,
                    "query_params": req_params,
                    "request_body": request_body_type,
                }
            )

    return endpoints


def main() -> None:
    endpoints = parse_controllers()
    OUTPUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "total_controllers": len({e["controller"] for e in endpoints}),
        "total_endpoints": len(endpoints),
        "endpoints": endpoints,
    }
    OUTPUT_YAML.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(
        f"Wrote {data['total_endpoints']} endpoints across {data['total_controllers']} controllers to {OUTPUT_YAML}"
    )


if __name__ == "__main__":
    main()

# Tooling status and reproducible continuation

Updated 18 October 2026 (Asia/Qatar).

## REA for Codex

The existing Cursor registration remains `npx -y rea-agents@6.5.0 mcp`. Codex's configuration previously contained node_repl, computer-use and codebase-memory-mcp, with no REA entry.

The reviewed Codex-only setup plan wrote `/Users/attiliab/.codex/config.toml` and created `/Users/attiliab/.codex/config.toml.rea.backup`. It added:

```toml
[mcp_servers.rea]
command = "/Users/attiliab/.npm/_npx/ad9a3fdbcad992c6/node_modules/.bin/rea"
args = ["mcp"]
startup_timeout_sec = 30
```

The installed version-42 skill already matched REA 6.5.0 and was not replaced. No Hopper, Ghidra, IDA, JADX, Java, Node, browser binaries or global toolchain upgrades were installed. A parsed TOML comparison confirmed that removing the new REA entry leaves the prior configuration unchanged. The cached launcher path is specific to this machine and depends on npm cache retention; if it disappears, rerun the scoped setup rather than changing Cursor or weakening client policies.

Post-setup doctor reports registration healthy. Missing native providers remain informational for this web task. A separate read-only MCP initialization/list/session check returned server rea 6.5.0, 207 tools and successful `binary_session`. The subprocess was terminated after verification. The active chat still did not expose REA tool functions; a Codex reconnect/restart is needed to load its new registration. Doctor success does not prove the current chat is connected.

Sanitized retained diagnostic files are in [08_TOOLING](../08_TOOLING/README.md). These verify readiness; they contain no Sentrix traffic.

## Browser and Playwright

The existing Chrome extension control supplied a supported Playwright locator interface and native screenshot/AX capture. The original tab detached during the turn boundary. The user re-enabled control; the original handle remained unattached, but a fresh research tab opened successfully in the same Chrome browser and retained login. The fresh tab was closed after the capture pass; the user-owned tab stayed open.

A separate Microsoft Playwright MCP package installation was attempted only because the user requested that setup. Automatic approval review rejected installing/executing unpinned `@playwright/mcp@latest`, describing it as unnecessary alongside existing browser controls. No workaround was used. **Standalone Playwright MCP remains uninstalled/unverified, and no independent Chrome CDP profile was launched.** The current research did not require either to collect the UI evidence.

If the user explicitly approves the separate installation, review a pinned official package and use a dedicated isolated profile with loopback/pipe debugging and no reuse or export of the normal Chrome profile. Manual login belongs to the user. Do not expose a CDP port externally, export authentication state or put cookies/tokens in the research archive. This describes the intended future setup, not work already completed.

## Sources consulted

- [Official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) — client registration and MCP configuration.
- [Microsoft Playwright MCP repository](https://github.com/microsoft/playwright-mcp) — official server, isolated profiles and browser options.
- Installed REA skill and connection/runtime references — scoped doctor/dry-run/setup, reconnect distinction and browser capture boundaries.

## Restart checkpoint

1. Read README, METHOD_SCOPE_AND_LIMITS, RESUME and the manifest before repeating captures.
2. Confirm REA appears in the active tool inventory; if not, reconnect Codex and inspect the launch failure rather than rerunning setup blindly.
3. Prefer the existing signed-in Chrome browser connection. A new isolated debugging session requires manual sign-in and a clear target; never copy the user's cookies.
4. Resume the ranked open questions, preserving evidence labels and avoiding business-record writes.

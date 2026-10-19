# Scripting, Connected Apps, Connections and Vibe

Research date: **2026-10-17**. Static official documentation only. No SDK initialization, account login, CLI installation, deployment, action execution, script execution or tenant inspection occurred. Product names, package names and channel recommendations are time-sensitive and should be rechecked before implementation.

## Observed extension surfaces

[Facilio Script Introduction](https://facilio.com/developers/docs/script-reference/index/) describes a platform-specific scripting language with syntax resembling JavaScript. It is used across workflows, lifecycle transitions, approvals, formulas, buttons, functions and schedules. [Execution Contexts](https://facilio.com/developers/docs/script-reference/execution-contexts/) separates event-bound record maps from standalone scheduler invocation. Do not assume this language is ordinary JavaScript or compatible with arbitrary npm libraries.

[Connected Apps Overview](https://facilio.com/developers/docs/connected-apps/index/) describes UI components hosted in embedded iframe/webview containers and communicating with Facilio through its Apps SDK. Its placement matrix includes full-page navigation tabs, record-summary tabs, replacement create/edit forms, related lists, dashboards and buttons. It also lists desktop-only panels and a mobile compatibility column. This is an integration surface inside the main product, with record/user context, events, data operations and interface commands.

[Vibe Overview](https://facilio.com/developers/docs/vibe/index/) describes standalone custom web applications on managed subdomains. It documents framework-independent static output, `@facilio/vibe-sdk`, browser identity, Connections actions and app-scoped functions/agents/files/realtime. The frontend remains a static application even when it invokes server-side functions. Vibe is therefore a separate application surface rather than another embedded widget placement.

[Facilio CLI Reference](https://facilio.com/developers/docs/vibe/cli-reference/) documents unified `@facilio/cli`, replacing the older Vibe-only package. Vibe commands manage apps/deployments and app-scoped services. Connections commands discover action descriptions and schemas, authorize linked accounts and execute actions. The page distinguishes read/write/destructive action semantics and describes registering app functions as catalog actions. Catalog scale figures are vendor claims, not independently enumerated evidence.

[Admin Connectors](https://facilio.com/help/docs/admin-guide/customization/connectors/) is another documented integration mechanism. The legacy [Help Connections page](https://facilio.com/help/docs/developer-guide/connections/) has little explanatory content. Avoid merging every occurrence of “Connected Apps,” “Connections” and “Connectors” into one architecture claim. Also distinguish platform reusable scripts from Vibe app functions.

## Atlas implementation opportunities — inference

Define extension contracts before building a plugin marketplace. A useful first version would offer a record-summary panel with limited context, scoped data access and a small event/interface bridge. This provides a practical route to charts, maps or specialist asset tools without replacing the whole product shell.

Separate embedded extensions from independently branded portals. An internal record panel needs lifecycle/context integration; a tenant/vendor portal needs its own navigation, identity rules and permitted actions. They can share domain services while offering different product experiences. A broad standalone hosting platform should follow proven portal requirements rather than precede them.

For integration and AI tools, an explicit action catalog is particularly valuable: action name, description, input/output schema, permission scope and operation semantics. Such a catalog can serve human developers, automation builders and assistants. All execution should still enforce the underlying business rules and produce audit records. This recommendation is not a claim about Facilio’s internal enforcement.

Initially favor a few supported extension points and curated integrations. Plan for package/API versioning, capability permissions, domain restrictions, error reporting, revocation and extension failure isolation. Keep customer credentials server-side. The richer the extension system becomes, the more important operational diagnostics and predictable compatibility become.

## Open questions

- Which extension capabilities are available in each edition or region?
- What are actual sandbox, timeout, dependency and resource limits?
- How do embedded apps inherit permissions, and how are publishers reviewed?
- How do Vibe functions/agents isolate secrets and customer data in practice?
- Which documentation examples represent production-supported behavior versus evolving features?

## REA analysis prompts

1. Diagram four distinct surfaces: platform scripting, embedded UI, integration actions and standalone apps.
2. Map the public widget matrix to Atlas’s real role-based journeys and mobile needs.
3. Specify the smallest useful Atlas extension SDK independently, including failure and permission states.
4. Rank portal, integration and AI capabilities by operational need before proposing a hosting/CLI platform.

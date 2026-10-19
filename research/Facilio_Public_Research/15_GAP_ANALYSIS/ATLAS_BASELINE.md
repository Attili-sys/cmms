# Atlas public baseline

Checked **2026-10-17** using public primary sources. This is a product-level baseline, not an audit of your installation or fork. Repository identity and feature parity with your deployed version remain unverified.

| Public source | What it establishes at product-description level |
|---|---|
| [Atlas homepage](https://atlas-cmms.com/) | Work orders, requests, preventive maintenance, mobile access, parts inventory and custom dashboards are already part of Atlas’s public proposition. |
| [Work-order feature page](https://atlas-cmms.com/features/work-orders) | Creation, assignment, task/checklist use, photos, search/filter/priority and mobile execution. |
| [Asset feature page](https://atlas-cmms.com/features/assets) | Asset hierarchy, documents, QR access, lifecycle information and preventive maintenance are already advertised. |
| [Atlas user guide](https://docs.atlas-cmms.com/) | A central maintenance model spanning assets, work scheduling, inventory and performance analysis. |
| [Public repository README](https://github.com/wurkado/atlas) | Describes time/history, trigger automation, reporting, equipment costs/downtime, stock alerts, purchase orders/approvals, service-provider assignments, roles/permissions and map-linked locations. The repository was read as public product documentation, not cloned or analyzed. |

Therefore “add work orders,” “add dashboards,” “add asset hierarchy,” “add approvals,” or “add automation” would be weak gap statements. The opportunity is to assess their **depth, integration and presentation** against the captured Facilio workflows.

No feature is marked absent merely because it was not mentioned on one public page. In particular, inspect your Atlas version’s purchasing, permissions, workflow, dashboard, location and vendor facilities before deciding to replace them.

The next implementation audit should establish your exact Atlas commit/version, enabled features, custom changes, entity relationships, permissions, existing extension contracts and representative user journeys. Use the codebase knowledge graph before file-based discovery, following the project’s AGENTS.md.

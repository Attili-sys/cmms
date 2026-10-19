<h1 align="center">AJ CAFM — Powered by Canvas</h1>

**AJ CAFM** is a self-hosted maintenance management system (CMMS / CAFM) running on **Canvas** (`https://aj-cafm--innovation.canvas.ajnai.net`) as well as Docker. It simplifies and automates the management of maintenance activities, work orders, preventive maintenance, assets, parts, locations, meters, checklists, and service requests.

**Example industries**

- Facilities Managers (buildings, property, real estate)
- Manufacturing/Production Teams (machinery and equipment)
- Healthcare Facilities (medical equipment maintenance)
- Hospitality Managers (hotels and resorts)
- Public Sector (infrastructure and public buildings)
- Educational Institutions (campus maintenance)
- Utility Companies (power, water, and energy systems)

**Screenshots**:
<div align="center">

![work_orders_screenshot.png](images/work_orders_screenshot.png)

</div>

## ⚡ **Features**

### Work Orders & Maintenance

- 📝 Create, assign, and track work orders.
- ⏱️ Log time, set priorities, and track history.
- 🤖 Automate work orders with preventive maintenance schedules and meter triggers.
- 📊 Export reports and view analytics.

### Analytics & Reporting

- 💼 Work order compliance and cost analysis.
- 🛠️ Equipment downtime and reliability insights.
- 💵 Cost trends and labor tracking.

### Equipment & Inventory

- ⚙️ Track equipment hierarchies, downtime, and maintenance costs.
- 📦 Manage parts and multi-part sets with stock alerts.
- 🛒 Automate purchase orders and approvals.

### User & Workflow Management

- 👥 Assign tasks to people, teams, or external vendors.
- 🧑‍💼 Customizable RBAC user roles and entity permissions.
- 🔄 Define conditional workflows with automation actions.

### Locations & Requests

- 📍 Manage hierarchical locations and floor plans.
- 📑 Create, approve, and track service requests.

---

## ☁️ Deploy on Canvas (`aj-cafm`) or Run Locally

### 1. Canvas Deployment (`atlas-cmms/`)

The Python 3.14 + FastAPI + SQLAlchemy 2.0 application (`atlas-cmms/`) bundles the compiled React SPA (`src/static/ui/`) and deploys directly to Canvas as **`aj-cafm`**:

```bash
cd atlas-cmms
.venv/bin/pytest -q && .venv/bin/ruff check .
canvas validate
canvas deploy
```

- **Live Canvas URL:** `https://aj-cafm--innovation.canvas.ajnai.net`
- **Local Development:**
  ```bash
  cd atlas-cmms
  PORT=8080 .venv/bin/python run.py
  ```

### 2. Legacy Docker Quick Start

1. Prepare configuration:
   - [docker-compose.yml](./docker-compose.yml)
   - [nginx.conf](./nginx.conf)
   - [.env.example](.env.example) → copy to `.env`
2. Run:
   ```bash
   docker-compose up -d
   ```
   Open http://localhost:3000 to access the application.

---

## 📚 Architecture & Engineering Documentation

| Document | Purpose |
|---|---|
| **[AGENTS.md](./AGENTS.md)** | Root operating guide for coding agents and contributors across all subprojects |
| **[atlas-cmms/README.md](./atlas-cmms/README.md)** | Canvas Python backend & bundled SPA overview, commands, and layout |
| **[atlas-cmms/DATABASE.md](./atlas-cmms/DATABASE.md)** | SQLAlchemy 2.0 / PostgreSQL schema reference (72 ORM models, 53 association tables, 44 enums, sequences, and tenant scoping) |
| **[atlas-cmms/API_CONTRACTS.md](./atlas-cmms/API_CONTRACTS.md)** | REST API router catalog, foreign-key mini-DTO hydration, hierarchy pagination, and `SearchCriteria` engine |
| **[atlas-cmms/MIGRATION_NOTES.md](./atlas-cmms/MIGRATION_NOTES.md)** | Java-to-Python migration architecture and Reviewer Agent verification notes |
| **[frontend/README.md](./frontend/README.md)** | React/TypeScript frontend architecture, build/lint commands, and static bundle sync |
| **[UNRESTRICTED_SELFHOSTED.md](./UNRESTRICTED_SELFHOSTED.md)** | Self-hosted capability policy (`CLOUD_VERSION=false`), branding changes, and retained security controls |
| **[GAP_ANALYSIS.md](./GAP_ANALYSIS.md)** | Reverse-engineered SentrixFM gap analysis (`S001–S107`), 18-domain comparison matrix, and `P0–P3` enhancement roadmap |
| **[FACILIO_GAP_ANALYSIS.md](./FACILIO_GAP_ANALYSIS.md)** | Reverse-engineered Facilio public research gap analysis (`22 REA targets`, 12 domains) and unified master CAFM roadmap |
| **[research/](./research)** | Reference research archives (`research/sentrixfm-research/` and `research/Facilio_Public_Research/`) |
| **[dev-docs/](./dev-docs)** | Operator guides (LDAP, TLS, backups, upgrades, factory reset) |

---

## 🔧 Environment Variables (Docker / Self-Hosted)

| Name                        | Required | Description                                                                                                                                                                                                                                                                                                         | Default Value         |
|-----------------------------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------|
| POSTGRES_USER               | Yes      | Postgres user                                                                                                                                                                                                                                                                                                       | rootUser              |
| POSTGRES_PWD                | Yes      | Postgres password                                                                                                                                                                                                                                                                                                   | mypassword            |
| MINIO_USER                  | Yes      | MinIO user                                                                                                                                                                                                                                                                                                          | minio                 |
| MINIO_PWD                   | Yes      | MinIO password                                                                                                                                                                                                                                                                                                      | minio123              |
| JWT_SECRET_KEY              | Yes      | JWT secret key. Generate with `openssl rand -base64 32`                                                                                                                                                                                                                                                             | your_jwt_secret       |
| PUBLIC_SERVER_URL           | No       | Website URL in this format `http://your.public.ip`                                                                                                                                                                                                                                                                  | http://localhost:3000 |
| ENABLE_EMAIL_NOTIFICATIONS  | No       | Enables or disables email notifications (`true` or `false`). Requires SMTP if enabled.                                                                                                                                                                                                                              | false                 |
| INVITATION_VIA_EMAIL        | No       | Enables or disables user invitations via email (`true` or `false`). Requires SMTP and ENABLE_EMAIL_NOTIFICATIONS if enabled.                                                                                                                                                                                        | false                 |
| MAIL_TYPE                   | No       | Mail type: `SMTP` or `SENDGRID`                                                                                                                                                                                                                                                                                     | smtp                  |
| SMTP_HOST                   | No       | The SMTP host                                                                                                                                                                                                                                                                                                       | smtp.gmail.com        |
| SMTP_PORT                   | No       | The SMTP port                                                                                                                                                                                                                                                                                                       | 587                   |
| SMTP_USER                   | No       | The SMTP username                                                                                                                                                                                                                                                                                                   | (empty)               |
| SMTP_PWD                    | No       | The SMTP password                                                                                                                                                                                                                                                                                                   | (empty)               |
| SMTP_FROM                   | No       | The SMTP from address, if different from the username.                                                                                                                                                                                                                                                              | (empty)               |
| SENDGRID_API_KEY            | No       | The Sendgrid API key                                                                                                                                                                                                                                                                                                | (empty)               |
| SENDGRID_FROM_EMAIL         | No       | The Sendgrid sender email                                                                                                                                                                                                                                                                                           | (empty)               |
| ALLOWED_ORGANIZATION_ADMINS | No       | Comma separated email addresses allowed to sign up without being invited, hence allowed to create organizations. Empty means everyone can create an organization                                                                                                                                                    | (empty)               |
| GOOGLE_KEY                  | No       | Google Maps API key                                                                                                                                                                                                                                                                                                 | (empty)               |
| GOOGLE_TRACKING_ID          | No       | Google Analytics tracking ID                                                                                                                                                                                                                                                                                        | (empty)               |
| STORAGE_TYPE                | No       | Type of storage either local MinIO or Google Cloud Storage `gcp` or `minio`                                                                                                                                                                                                                                         | minio                 |
| GCP_JSON                    | No       | The Google Cloud JSON key after following [these instructions](./GCP-setup.md).                                                                                                                                                                                                                                     | (empty)               |
| GCP_PROJECT_ID              | No       | The Google Cloud project ID, also found in the `GCP_JSON` file.                                                                                                                                                                                                                                                     | (empty)               |
| GCP_BUCKET_NAME             | No       | GCP Bucket Name                                                                                                                                                                                                                                                                                                     | (empty)               |
| MAIL_RECIPIENTS             | No       | Comma-separated email addresses of the super admins where to send information emails like new signups.                                                                                                                                                                                                              | (empty)               |
| ENABLE_SSO                  | No       | Enables or disables SSO (`true` or `false`). Requires `OAUTH2_PROVIDER`, `OAUTH2_CLIENT_ID` and `OAUTH2_CLIENT_SECRET`.                                                                                                                                                                                             | false                 |
| OAUTH2_PROVIDER             | No       | OAuth2 provider `google` or `microsoft`                                                                                                                                                                                                                                                                             | (empty)               |
| OAUTH2_CLIENT_ID            | No       | OAuth2 Client ID                                                                                                                                                                                                                                                                                                    | (empty)               |
| OAUTH2_CLIENT_SECRET        | No       | OAuth2 client secret                                                                                                                                                                                                                                                                                                | (empty)               |
| CUSTOM_COLORS               | No       | Custom colors in JSON format (hexadecimal).                                                                                                                                                                                                                                                                         | (empty)               |
| BRAND_CONFIG                | No       | Brand config for white labeling (`{ "name": "Powered by Canvas", "shortName": "Canvas" }`).                                                                                                                                                                                                                         | (empty)               |
| SOURCE_CODE_URL             | Yes      | Public URL for the exact Corresponding Source used to build the deployed images.                                                                                                                                                                                                                                    | repository URL        |
| LDAP_ENABLED                | No       | Enables or disables LDAP. Full list in [LDAP_SETUP.md](./dev-docs/LDAP_SETUP.md).                                                                                                                                                                                                                                   | false                 |

---

## 🌐 Supported Languages

English, Spanish, French, German, Turkish, Polish, Portuguese (Brazil), Arabic, Swedish, Italian, Russian, Dutch, Chinese, Hungarian, Bosnian, Japanese.

## 🏗️ **Tech Stack**

- **[Canvas Backend & Bundled SPA](atlas-cmms)** — Python 3.14, FastAPI, SQLAlchemy 2.0, `ajnkit-core`, Alembic
- **[Web Frontend](frontend)** — React, TypeScript, Redux Toolkit, MUI ("Powered by Canvas")
- **[Legacy Backend Reference](api)** — Java 17, Spring Boot, Liquibase
- **[Mobile App](mobile)** — React Native (Expo)

## Open Source Licensing Info

This self-hosted edition is distributed under the [GNU AGPLv3](./LICENSE). Existing features implemented in this source tree are available without a commercial subscription, activation key, license file, or periodic licensing-service connection. Set `SOURCE_CODE_URL` to the public Corresponding Source for the exact version you deploy. See [UNRESTRICTED_SELFHOSTED.md](./UNRESTRICTED_SELFHOSTED.md) for policy, verification, build, and deployment details.

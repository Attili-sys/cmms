# Atlas CMMS

Self-hosted maintenance system. The product in this repo is three apps: a Java API (`api/`), a React web app (`frontend/`), and an Expo mobile app (`mobile/`). `home/` is the marketing site. `cmms/` is a separate Canvas app with its own `cmms/AGENTS.md`; follow that file when the task is about `cmms/`, and leave `cmms/` alone otherwise.

`README.MD` is for people installing the product. This file is the operating sheet for coding agents.

## Commands

Run these from the directory named in the heading. They are the commands checked into the repo. A green result still has to be the output of a command you just ran.

| App | Command | Source |
|---|---|---|
| Full stack | `docker-compose up -d`, then http://localhost:3000 | `README.MD`, `docker-compose.yml` |
| API run | JDK 17, Postgres credentials in `api/src/main/resources/application-dev.yml`, then `mvn spring-boot:run` | `api/README.md`, `api/pom.xml` (`java.version` 17, Spring Boot 3.5.16) |
| API tests | `mvn test` | `api/.agent-docs/SERVICE-REFACTORING-GUIDE.md` |
| API coverage for one class | `mvn -o prepare-package -Dtest=AssetServiceTest` | `api/src/test/java/com/grash/agents.md` |
| Web | `npm start`, `npm run lint`, `npm run build` | `frontend/package.json` |
| Mobile | `npm install`, then `npm test`, `npm run android`, or `npm run ios` | `mobile/package.json`, `mobile/CONTRIBUTING.md` |

`frontend/package.json` has no `test` script. Do not invent one.

## Where new code goes

| Change | Place |
|---|---|
| API Java | `api/src/main/java/com/grash/` |
| API schema | Liquibase changelogs under `api/src/main/resources/` |
| Web pages | `frontend/src/content/own/` |
| Web strings | `frontend/src/i18n/translations/` |
| Mobile | `mobile/` |

Business logic belongs in the API service layer. The completed example is `RequestController` / `RequestService`, described in `api/.agent-docs/SERVICE-REFACTORING-GUIDE.md`.

## Rules that are easy to miss

Schema (`api/src/main/resources/db/Agents.md`):

- Every foreign key sets `onDelete=Cascade`, or `onDelete=Set null` when the column is nullable.
- A new table that extends `CompanyAudit` also adds `<createSequence sequenceName="new_table_seq" startValue="1" incrementBy="50"/>`.

API tests (`api/src/test/java/com/grash/agents.md`):

- Unit tests use `MockitoExtension`, `@Mock`, and `@InjectMocks`. They do not load a Spring context.
- Controller tests use `@WebMvcTest` and `MockMvc`. They do not load a Spring context.
- `@SpringBootTest` is for integration tests only. Name those `*IntegrationTest.java`.
- Unit and controller tests are named `<ClassName>Test.java`.

Translations (`frontend/src/i18n/translations/AGENTS.md`):

- Translate values only. Leave keys unchanged.

Secrets stay in `.env` and the environment. Never commit them.

## Read when

| File | Read when |
|---|---|
| `api/src/test/java/com/grash/agents.md` | Writing or changing API tests, or quoting JaCoCo numbers |
| `api/src/main/resources/db/Agents.md` | Adding a table or a foreign key |
| `api/.agent-docs/SERVICE-REFACTORING-GUIDE.md` | Moving logic out of a controller |
| `frontend/src/i18n/translations/AGENTS.md` | Editing translation JSON |
| `dev-docs/` | Super-admin, LDAP, TLS, backup, upgrades |
| `ATLAS_CAFM_DECISION_REPORT.md` | Choosing what to build next. It is an audit, not a description of code you have changed |
| `UNRESTRICTED_SELFHOSTED.md` | Understanding which restrictions were removed on this branch and which controls are retained |
| `cmms/AGENTS.md` | Any task inside `cmms/` |

The three instruction files under `api/` and `frontend/` are not named `AGENTS.md` in a way every tool will auto-load (`Agents.md` and `agents.md`). Open them by the paths above.

## Self-hosted edition (this branch)

This branch (`unrestricted-selfhosted`) removes all commercial restrictions. The capability policy is:

> When `CLOUD_VERSION=false`, every implemented feature is available without a subscription, activation key, license file, numerical quota, trial period, or connection to a licensing service.

Rules for agents working on this branch:

- **Do not re-add** Keygen validation, Paddle billing checks, license-file reads, trial-expiry scheduling, or feature-count quotas in any self-hosted code path.
- `LicenseService.isUnrestrictedSelfHosted()` is the single gating method. Guard any cloud-only branch with `if (!licenseService.isUnrestrictedSelfHosted())` or `if (cloudVersion)`, not the reverse.
- `SubscriptionPlan.getFeatures()` always returns `EnumSet.allOf(PlanFeatures.class)`. Do not use stored plan features as a gate; do not revert this getter.
- Authentication, role/entity permissions, company isolation, approval rules, rate limits, and audit logging are **not** commercial restrictions and must remain unchanged.
- Tests that assert an operation is forbidden due to a plan feature or user quota are testing removed behavior. Replace them with tests that assert the operation succeeds despite an empty stored features set or a low quota value.

## Done

An API change is done when the matching `mvn` test command has been run and its summary is in the reply. A web change is done when `npm run lint` has been run in `frontend/`. A mobile change is done when `npm test` has been run in `mobile/`. A UI change is done when the affected screen has been used in a browser, not only inspected as a screenshot.

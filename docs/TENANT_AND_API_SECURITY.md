# Tenant isolation and SOC API security

## Supported deployment boundary

CyberFortress currently supports **one tenant per runtime**. The agent model uses process-wide configuration and long-running workers; it does not yet provide request-scoped tenant contexts for multiple clients sharing one process. The runtime therefore refuses SOC API requests and IR/SIEM processing when more than one real tenant configuration is present.

The sample `config/tenants/example_client` is a template and is not counted as an active tenant. For each real client, deploy a separate CyberFortress installation/runtime, with separate service account, secrets, environment, logs, evidence, backups and network boundary. Do not configure multiple client tenants in one runtime.

Set `CF_TENANT_ID` to the tenant directory name for that runtime. If a single real tenant is configured, the active process tenant must match it. Tenant identifiers are validated before they are used in paths. Tenant symlinks are ignored.

The tenant orchestrator is inventory-only. It must not mutate process-wide tenant environment variables to impersonate multiple clients.

## SOC API authentication and authorization

The SOC API binds to loopback by default. It requires an authenticated Basic or Bearer identity; anonymous access is denied regardless of `CF_SOC_REQUIRE_AUTH`. Configure users in `.env`:

```dotenv
CF_SOC_USERS=analyst:analyst:REPLACE_WITH_RANDOM_TOKEN,operator:operator:REPLACE_WITH_RANDOM_TOKEN
CF_SIEM_REQUIRE_TOKEN=true
CF_SIEM_INGEST_TOKEN=REPLACE_WITH_DIFFERENT_RANDOM_TOKEN
CF_MAX_BODY_BYTES=262144
CF_RATE_LIMIT_MAX=120
CF_RATE_LIMIT_WINDOW=60
```

Roles are `viewer`, `analyst`, `operator` and `admin`. Ingest requires both an authorized role with `write:ingest` and the separate SIEM ingest token. Missing roles and unknown roles fail closed. Unknown routes are not served. Request bodies above the configured maximum are rejected with HTTP 413.

Do not expose the SOC API directly to the internet. If remote access is required, place it behind an approved TLS reverse proxy, restrict source networks, and manage certificates and identity at that boundary. Never reuse the dashboard password as an ingest token.

## Verification boundary

CI covers RBAC denial, tenant-context mismatch, shared-runtime refusal, symlink exclusion, caller-supplied tenant-field stripping, request routing and static deployment privilege policy. CI does not prove tenant separation on a real host, proxy configuration, or client operational controls. Those remain owner-run validation gates.

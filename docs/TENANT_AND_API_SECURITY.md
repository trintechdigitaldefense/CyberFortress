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

Roles are `viewer`, `investigator`, `auditor`, `analyst`, `operator` and `admin`. Viewer, investigator and auditor are read-only; analysts can ingest and manage case/evidence data; operators can approve Tier-2 actions; admins have the full permission set. Ingest requires both an authorized role with `write:ingest` and the separate SIEM ingest token. Missing roles and unknown roles fail closed. Unknown routes are not served. Request bodies above the configured maximum are rejected with HTTP 413.

Do not expose the SOC API directly to the internet. If remote access is required, place it behind an approved TLS reverse proxy, restrict source networks, and manage certificates and identity at that boundary. Never reuse the dashboard password as an ingest token.

## Verification boundary

CI covers RBAC denial, tenant-context mismatch, shared-runtime refusal, symlink exclusion, caller-supplied tenant-field stripping, request routing and static deployment privilege policy. CI does not prove tenant separation on a real host, proxy configuration, or client operational controls. Those remain owner-run validation gates.


## Defensive threat review

| Threat / failure mode | Implemented control | Regression evidence |
|---|---|---|
| Anonymous access or unknown-role privilege | SOC API requires configured identity; missing/unknown roles deny; dashboard write roles are explicit | SOC auth/RBAC unit tests; dashboard/API security gate |
| Credential confusion between services | SOC API bearer identities come only from `CF_SOC_USERS`; dashboard password is not accepted as an SOC bearer token; SIEM ingest has a separate token | SOC bearer regression tests |
| Cross-tenant reads/writes through dashboard or SOC routes | Both HTTP handlers check the isolated-runtime guard before route dispatch; background agents and case-store construction also reject shared multi-tenant execution | Tenant-boundary tests and deployment security regression |
| Client tenant spoofing | SIEM strips `tenant_id` and `tenant` claims and stamps only the active process tenant; a request claim cannot create tenant context | SIEM tenant spoofing and tenant-context tests |
| Tenant path traversal / symlink escape | Tenant IDs are validated; tenant root, tenant directory and settings symlinks are rejected; malformed settings fail closed | Tenant path and settings regression tests |
| API brute force / request flooding | Per-client rate limiting occurs before authentication on SOC and dashboard routes | API source gate and existing rate-limit implementation |
| Oversized or abusive SIEM payload | HTTP body cap, batch-count cap, event object validation, bounded field lengths and severity allowlist | SIEM batch/schema tests and SOC API route tests |
| Browser cross-site state mutation | Dashboard state-changing POST routes require the custom request header and a write-capable role | Existing dashboard CSRF/RBAC tests |
| Approval replay or unauthorized containment | Nonce expiry/one-time consumption, signature verification, ROE allowlist and Tier-2 approval remain separate gates | WhatsApp approval and ROE regression suite |

### Residual risks and explicit limits

- Concurrent multi-tenant workers in one process are **not supported**. A future design would need tenant-scoped principals, request context, queue partitioning, storage partitioning and per-tenant worker lifecycles before that feature can be enabled.
- The application does not terminate public TLS. Remote dashboard/API access requires a separately reviewed TLS reverse proxy, network allowlist and certificate lifecycle.
- CI cannot prove host filesystem ownership, systemd capability behaviour, actual firewall kernel support, client network boundaries or operational recovery on the owner's VM.
- A green CI run does not replace independent security review, owner-run monitoring soak or client-specific legal/Rules-of-Engagement approval.

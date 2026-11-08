# CyberFortress — Security Acceptance Criteria

**Release target:** 1.0.0  
**Default posture:** MONITORING ONLY  
**Live containment:** DISABLED unless every applicable gate is independently satisfied.

## Non-negotiable controls

### Authorisation and engagement scope
- No valid client sign-off: deny live containment.
- Invalid, expired, revoked or mismatched engagement: deny.
- Action not explicitly listed in authorised actions: deny.
- Target outside the engagement's explicit scope: deny.
- Scope validation must be repeated immediately before execution.
- Monitoring and dry-run paths remain usable without containment sign-off.

### Human approval
- High-impact actions require a verified, attributable human approval.
- Approval must bind to a specific action, target, client, engagement and expiry.
- Approval tokens/nonces must be unpredictable, short-lived and single-use.
- Replays, unknown approvers, invalid signatures and expired approvals are rejected.
- Approval and execution must be atomic/idempotent so retries cannot execute twice.

### Audit and evidence
- Every privileged decision and attempted action is attributable.
- Audit-chain corruption, append failure or unavailable storage blocks protected action.
- No unchained fallback is permitted for security decisions.
- Audit verification must detect malformed entries, missing hashes, broken links, truncation and tampering.
- Evidence exports include hashes and verification outcome; missing evidence is reported as missing.

### Dashboard and APIs
- Remote interfaces require authentication.
- Permissions are checked server-side for every privileged endpoint.
- CSRF, session expiry, rate limiting, secure headers and input validation are enforced.
- Read-only roles cannot invoke response, approval, configuration or administrative operations.
- Tenant identity is derived from trusted authenticated context, not a client-supplied tenant field.
- Cross-tenant reads and writes are denied and tested.

### Firewall containment
- Monitoring/dry-run is default.
- Only explicitly authorised targets are eligible.
- Operator, management, gateway and monitoring infrastructure are protected from blocking.
- Unrelated host firewall policy is not modified.
- Apply operations are verified; partial failure triggers safe rollback or an explicit degraded state.
- Recovery instructions are tested on an isolated VM.
- No live firewall testing on customer infrastructure during development.

### Runtime and supply chain
- Agents run with least privilege.
- Secrets are not committed or logged.
- Dependencies are pinned/controlled and audited.
- Disk, memory, queue and request limits are enforced.
- Failure, restart, backup and restore behaviour are tested.
- Termux/proot capability limits are documented; do not assume systemd or CAP_NET_ADMIN.

## Current hardening evidence (2026-11-08)

- P0/P1 code-level security controls and the P2 automated firewall/deployment/recovery checks pass on hardening commit `d1a274838f8bf33187fd2f6d8f3d7a732d215c90`.
- CI run [42526197795](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42526197795) passed Ruff, 128 pytest tests, Bandit, pip-audit, audit-chain and defense-posture checks, shell syntax, isolated firewall acceptance, backup/restore acceptance and deployment-profile safety.
- The isolated namespace test exercised effective NET_ADMIN chain/rule creation, bidirectional DROP verification, explicit unblock, emergency disarm and empty-chain read-back. It did not modify the runner's host firewall or any client network.
- Backup/recovery acceptance created a synthetic off-box backup, verified its SHA-256 sidecar, staged the archive without overwriting live files, excluded pending WhatsApp approval requests and decision data and refused a second restore into an existing staging directory.
- Standard Docker Compose and Termux/proot are monitoring-only. Native Linux VM is the candidate live-containment profile.
- Actual client VM installation, host capability output, seven-day monitoring soak, client-specific allowlist/ROE, witnessed backup restore, legal/E&O evidence and client-approved containment change window remain outstanding.
- These results do not establish client readiness, live containment authorisation, or v1.0.0 acceptance.

## Required evidence before v1.0.0
1. CI run with Ruff, pytest, Bandit and pip-audit passing.
2. Concurrency and failure tests for metrics and audit.
3. Webhook signature, nonce, replay and approver tests.
4. Missing/invalid/expired ROE denial tests.
5. Autonomy driver-failure and approval tests.
6. Dashboard role/CSRF/session tests.
7. Cross-tenant adversarial tests.
8. Mocked firewall suite and isolated Linux VM apply/verify/rollback report.
9. End-to-end synthetic event → detection → case → evidence → approval → simulated response → audit test.
10. Installation, upgrade, backup and restore evidence for each supported deployment profile.
11. Pilot soak report and independent technical review.
12. Client-specific legal/engagement sign-off before any live containment.

Passing software tests does not constitute legal approval or client deployment authorisation.

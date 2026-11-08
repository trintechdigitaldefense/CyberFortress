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

## Current hardening evidence (2026-11-08)\n\n- P0 code-level security gate is passing on hardening commit `3751b7058694498421ff98d58e70b9ff6a919c65`.\n- CI run [42522941703](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42522941703) passed Ruff, 128 pytest tests, Bandit, pip-audit, audit-chain script, defense-posture script, shell syntax checks and isolated firewall namespace acceptance.\n- Firewall acceptance tests use mocked host commands only. They cover exact client ROE action matching, partial insertion rollback, and rollback read-back failure. No live host firewall or client network was modified.\n- The isolated-network-namespace harness `scripts/firewall_namespace_acceptance.sh` passed on the ephemeral GitHub-hosted Ubuntu runner. It created a loopback-only namespace, applied and bidirectionally verified DROP rules, removed them using the exact rule specification, verified rollback, and deleted the namespace. This is not a client VM or client-network test.\n- Isolated Linux VM apply/verify/rollback evidence remains outstanding. Termux/proot deployments remain monitoring-only unless the required host capabilities and separately approved deployment profile are present.\n- These results do not establish client readiness, live containment authorisation, or v1.0.0 acceptance.\n\n## Required evidence before v1.0.0
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

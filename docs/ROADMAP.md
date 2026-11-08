# CyberFortress engineering roadmap

**Development branch:** `hardening/cyberfortress-final-release`  
**Baseline:** `0a1f61a4681f3f2205a3ec6802e103932658daaf`  
**Operating posture:** monitoring-only; `CF_CONTAINMENT_LIVE=false`  
**Release target:** v1.0.0 (not released)

This roadmap separates work that can be completed in the repository from acceptance evidence that must be collected by TrinTech on its own isolated virtual machine. No cloud VM will be provisioned as part of this plan.

## Current verified baseline

The latest checked GitHub Actions run for the baseline, [42526663705](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42526663705), completed successfully. The repository's acceptance record reports 128 pytest tests plus Ruff, Bandit, pip-audit, shell checks, isolated firewall-namespace acceptance, backup/restore acceptance and deployment-profile safety checks.

These are CI results, not proof of a clean installation or live host capability on a real VM. The current branch remains a release candidate, not a client-ready release.

## Engineering roadmap

### R1 — Repository and release-record reconciliation
- [ ] Make README, VERSION, CHANGELOG, QUALITY_STATUS, HARDENING_STATUS and FEATURE_REGISTER agree on the same version, commit and test count.
- [ ] Remove stale pilot-ready/client-ready wording where it overstates evidence.
- [ ] Keep a single authoritative feature register; each status must link to concrete tests or evidence.
- [ ] Make CI output and release-gate instructions reproducible from a clean clone.

**Exit:** no conflicting version, test-count or readiness claims; clean CI on the updated branch.

### R2 — Runtime, installation and recovery reliability
- [x] Harden local start/stop lifecycle: repeated starts skip already-running recorded agents; shutdown validates PID identity and never kills unrelated listeners by port; stale/reused PID records are handled conservatively. A regression check is enforced in CI. (Install/update/uninstall audit remains open.)
- [ ] Verify all supported profiles and ensure Termux/proot and standard Docker remain monitoring-only.
- [ ] Review systemd service users, filesystem permissions, restart policy, resource limits and shutdown ordering.
- [ ] Exercise backup/restore code paths, including malformed archives, interrupted copies, disk-full and permission failures.
- [ ] Ensure secrets, client sign-off and approval state are never copied into public or ordinary operational backups.

**Exit:** automated clean-install, upgrade, restart, failure-injection and staged-restore checks pass in CI; no unsafe privilege escalation or accidental live-mode activation.

### R3 — Security and tenant-boundary assurance
- [ ] Complete endpoint-by-endpoint authentication, authorization, CSRF, session, rate-limit and input-validation review.
- [ ] Complete cross-tenant adversarial tests for every API, case, evidence, dashboard and export path.
- [ ] Review approval binding, nonce/replay handling, expiry, approver identity and idempotent execution.
- [ ] Review audit-chain concurrency, tamper handling, permissions, storage failure and recovery.
- [ ] Review telemetry ingestion limits, schema validation, queue/backpressure behaviour and untrusted indicator handling.
- [ ] Verify dependency pinning, vulnerability scanning and secret-leak checks remain blocking CI gates.

**Exit:** documented threat review; adversarial regression tests pass; no unresolved critical/high security defect.

### R4 — End-to-end SOC and operator workflow
- [ ] Prove synthetic event → normalization → detection → case → investigation → evidence → approval decision → simulated response → immutable audit trail.
- [ ] Verify playbook dry-run, authorization, idempotency, timeout and rollback behaviour.
- [ ] Verify alert/report delivery failure does not silently drop cases or weaken approval gates.
- [ ] Validate dashboard health and agent status against actual process heartbeats.
- [ ] Produce operator troubleshooting, incident handling, evidence export and emergency-disarm runbooks.

**Exit:** repeatable synthetic end-to-end tests pass; all operator actions are attributable; failure states are visible and fail safely.

### R5 — Documentation and release candidate packaging
- [ ] Finish the installation guide, configuration reference, supported-platform matrix and troubleshooting guide.
- [ ] Publish a concise operator quick-start and command cheatsheet.
- [ ] Document data flows, ports, permissions, secrets, retention and backup boundaries.
- [ ] Reconcile release notes and version authority; prepare a release-candidate checklist and rollback instructions.
- [ ] Run the full CI release gate against the exact final commit.

**Exit:** a clean-clone handover is complete and the branch is internally consistent. No v1.0.0 tag until all required gates are satisfied.

## Owner-run validation after engineering completion

After R1–R5 engineering work is complete and the final candidate is pushed, TrinTech will clone the branch and perform validation on its own isolated VM. The handover will include exact commit SHA, install commands, test commands, expected results and a results template.

The owner-run validation must cover:
- clean install, upgrade and restart on the intended Ubuntu/Debian VM;
- actual host/kernel/firewall backend and effective capability probe;
- monitoring-only soak (minimum seven days for the current operational acceptance plan);
- synthetic end-to-end detection and evidence workflow;
- backup transfer and witnessed staged restore;
- emergency disarm and recovery drill;
- logs and CI/host evidence attached to the acceptance record.

If a host test fails, the issue returns to engineering and the affected gate is rerun. No client network is used for development testing.

## Separate legal and client gates

These cannot be completed by code changes or by CI:
- client-specific signed NDA and Rules of Engagement;
- counsel review and appropriate E&O coverage;
- client allowlist, authorized action scope and named approvers;
- client-approved maintenance/containment window and operator acknowledgement.

Live containment stays disabled until the technical, operational and legal gates are independently satisfied. P3/SOC production acceptance and v1.0.0 release approval must not be inferred from CI success alone.

## Working rules

- All engineering changes are committed to `hardening/cyberfortress-final-release` unless a separate reviewed branch is explicitly agreed.
- Never force-push, merge to `main`, publish a release tag or enable live containment as a shortcut.
- CI is run after meaningful changes; failures are fixed before the next gate.
- Report only verified changes, commits and test outcomes.

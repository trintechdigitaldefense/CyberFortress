# CyberFortress engineering roadmap

**Development branch:** `hardening/cyberfortress-final-release`  
**Latest R2/R3 verified code checkpoint:** `1ccc6712488ccb6be71a16e006fdf9eef59411b7`  
**Operating posture:** monitoring-only; `CF_CONTAINMENT_LIVE=false`  
**Release target:** v1.0.0 (not released)

This roadmap separates work that can be completed in the repository from acceptance evidence that must be collected by TrinTech on its own isolated virtual machine. No cloud VM will be provisioned as part of this plan.

## Current verified checkpoint

GitHub Actions [run #416](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42617182784) passed on `1ccc6712488ccb6be71a16e006fdf9eef59411b7`: 141 pytest tests, Ruff, Bandit, pip-audit, isolated installer smoke test, process lifecycle safety, safe environment parsing, fast-forward upgrade/rollback regression, least-privilege systemd and tenant-boundary checks, isolated firewall namespace acceptance, malicious archive rejection, backup/restore failure-injection acceptance, and Docker/Termux monitoring-only profile checks. This closes the R2 and R3 engineering CI gates; owner-run VM validation remains separate.

This verifies the R2/R3 engineering gates in CI. It does not prove the owner's host filesystem permissions, systemd capability behaviour, live host firewall backend, client network isolation, or operational recovery. Those remain owner-run VM gates.

## Engineering roadmap

### R1 — Repository and release-record reconciliation
- [ ] Make README, VERSION, CHANGELOG, QUALITY_STATUS, HARDENING_STATUS and FEATURE_REGISTER agree on the same version, commit and test count.
- [ ] Remove stale pilot-ready/client-ready wording where it overstates evidence.
- [ ] Keep a single authoritative feature register; each status must link to concrete tests or evidence.
- [ ] Make CI output and release-gate instructions reproducible from a clean clone.

**Exit:** no conflicting version, test-count or readiness claims; clean CI on the updated branch.

### R2 — Runtime, installation and recovery reliability
- [x] Harden local start/stop lifecycle: duplicate starts are suppressed only for verified recorded agents; shutdown validates PID identity and never kills unrelated listeners or clears ports.
- [x] Verify supported profiles: Termux/proot and standard Docker remain monitoring-only.
- [x] Review systemd service users, filesystem permissions, restart policy, resource limits and shutdown ordering. Standard agents use a dedicated unprivileged account; firewall privileges are bounded to network capabilities.
- [x] Exercise backup/restore paths, including checksum mismatch, traversal and symlink archives, interrupted copy, simulated storage-write failure, destination failure and no-overwrite staging.
- [x] Keep secrets, sign-off material and pending approval state outside operational backups.
- [x] Add isolated-venv installation, fast-forward-only upgrade, dirty-tree/divergence refusal and source rollback reference.

**Exit: Engineering gate complete.** CI run #416 passed installer smoke, upgrade regression, lifecycle safety, deployment privilege checks and backup/restore failure injection. Owner-run VM validation remains separate.
### R3 — Security and tenant-boundary assurance
- [x] Complete endpoint-by-endpoint authentication, authorization, CSRF, stateless-auth/session and rate-limit/input-validation review for the dashboard and SOC API.
- [x] Enforce one tenant per isolated runtime at background-agent, case-store, dashboard and SOC API boundaries; refuse shared-process multi-tenant operation. Tenant IDs, directory symlinks and settings files are validated.
- [x] Add cross-tenant adversarial regressions for untrusted tenant claims, tenant mismatch, shared-runtime refusal, path traversal and symlinked settings. Both dashboard and SOC API enforce the same runtime guard before dispatching routes.
- [x] Review approval binding, nonce/replay handling, expiry, approver identity and idempotent execution; existing approval/ROE regressions remain blocking.
- [x] Review audit-chain tamper/concurrency and storage-failure controls; existing audit acceptance remains blocking.
- [x] Bound SIEM request body, batch count, field sizes and severity schema; strip caller tenant aliases and stamp only the trusted process tenant.
- [x] Keep dependency pins, Bandit and pip-audit as blocking CI gates.
- [x] Publish the threat review and explicit residual-risk statement in [TENANT_AND_API_SECURITY.md](TENANT_AND_API_SECURITY.md).

**Exit: Engineering gate complete.** CI run #416 passed 141 tests, Ruff, Bandit, pip-audit and tenant/API security regressions. Shared-process multi-tenant deployment remains intentionally unsupported; use one isolated runtime per client. External review and owner-run host validation are not implied.
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

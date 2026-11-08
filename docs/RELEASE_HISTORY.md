# CyberFortress — Release History and Version Authority

## Version authority

The root `VERSION` file is the authoritative development version. At the reviewed hardening baseline it declares **0.6.0-rc1**.

## Baseline discrepancy requiring reconciliation

- `README.md` displays **v0.3.11**.
- `VERSION` displays **0.6.0-rc1**.
- `docs/QUALITY_STATUS.md` describes **0.6.0-rc1**.
- `CHANGELOG.md` must be checked and reconciled with the above.

The README's old version and any outdated readiness/marketing claims must be corrected only after the release facts are confirmed. Do not invent a released version or imply client readiness.

## Release policy

- Development commits stay on `hardening/cyberfortress-final-release`.
- Every release candidate has a unique version and linked commit.
- Release notes list changes, known limitations, test evidence and deployment constraints.
- v1.0.0 is tagged only after all finalisation gates and client-acceptance evidence pass.
- Live containment approval is separate from software versioning.

## Baseline

| Track | Meaning | Evidence |
|---|---|---|
| 0.6.0-rc1 | Current hardening development track | Root `VERSION` at baseline commit `eaffd671f5802d2c20b80110f624b9aac0f868bf` |
| 1.0.0 | Target final release | Not released; all acceptance gates outstanding |


## 2026-11-08 hardening checkpoint (not a release)

- Hardening branch head at checkpoint: `3751b7058694498421ff98d58e70b9ff6a919c65`.
- CI run: [42522941703](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42522941703) — all configured checks passed, including 128 tests, Ruff, Bandit, pip-audit and isolated firewall namespace apply/verify/rollback.
- P0 security controls have passed their current automated gate.
- Mocked firewall acceptance and isolated network-namespace apply/verify/rollback have passed on an ephemeral Ubuntu CI VM. Client-specific deployment/recovery evidence and all remaining roadmap gates are still outstanding.
- No version tag was created. v1.0.0 remains unreleased and CyberFortress is not yet client-ready.

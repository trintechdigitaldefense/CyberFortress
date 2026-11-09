# Quality status

**Version track:** 0.6.0-rc1 / hardening branch  
**Live containment:** **NOT approved** by default — MONITORING only until legal + VM soak + sign-off.

This file is an **honest** status board. Scores are not marketing claims.

| Area | Status | Notes |
|------|--------|-------|
| Safety defaults | Strong | `CF_CONTAINMENT_LIVE=false` default; ROE gates on live DROP |
| Metrics concurrency | Fixed (P0) | Deadlock removed; atomic persist; unit tests |
| Audit chain | Fixed (P0) | Flock, fail-closed, no unchained fusion fallback |
| Dashboard / SOC API auth | Hardened (P1) | Fail-closed roles, dedicated SOC API credentials, read-only roles, rate limits before auth, CSRF header on dashboard POST |
| WhatsApp approvals | Hardened (P1) | Signature required when enabled; nonce/admin checks |
| Firewall validation | Hardened (P1) | Hostname/CIDR/loopback/ROE denial tests |
| CI | Blocking | Ruff, pytest, Bandit, pip-audit — no silent failure suppression |
| IR case store | Improved (P2) | Path-safe IDs, tenant filter, atomic write, transitions |
| Tenant isolation | Engineering gate complete (P2) | One tenant per isolated runtime; agent, case-store, dashboard and SOC API guards; shared-process multi-tenant mode refused |
| Telemetry schema | Done (P3) | v1.0 validate/normalize |
| Readiness layers | Done (P4) | software → monitoring → pilot → live |
| Release tests | CI verified | 141 tests plus installer, upgrade, lifecycle, firewall and backup/restore failure-injection gates |
| Isolated VM soak | **Required** | See `docs/PILOT_SOAK.md` |
| Legal / ROE / E&O | **Required** | See `docs/LEGAL_GATE.md` |

## Latest CI evidence

[Run #408](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42614223976) passed on `a3a50bd2823aa55f8223378d0158596196001d2d`: 141 tests, Ruff, Bandit, pip-audit, installer smoke, upgrade/lifecycle/tenant security regressions, firewall namespace acceptance and backup/restore failure injection. Owner-run VM validation remains required.

## Verify locally

```bash
bash scripts/quality_check.sh
bash scripts/release_gate.sh
python3 -m pytest tests/ -q
bash scripts/pilot_vm_preflight.sh   # on real VM
```

## Do not claim

- "Production-ready live containment" without soak + legal gate
- "Fully automatic defense" — response is rules-driven and gated

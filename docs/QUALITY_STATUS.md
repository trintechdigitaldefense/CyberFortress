# Quality status

**Version track:** hardening branch / post–Phase 1–2 start  
**Live containment:** **NOT approved** by default — MONITORING only until legal + VM soak + sign-off.

This file is an **honest** status board. Scores are not marketing claims.

| Area | Status | Notes |
|------|--------|-------|
| Safety defaults | Strong | `CF_CONTAINMENT_LIVE=false` default; ROE gates on live DROP |
| Metrics concurrency | Fixed (P0) | Deadlock removed; atomic persist; unit tests |
| Audit chain | Fixed (P0) | Flock, fail-closed, no unchained fusion fallback |
| Dashboard auth | Hardened (P1) | Required auth policy, roles, CSRF header on POST |
| WhatsApp approvals | Hardened (P1) | Signature required when enabled; nonce/admin checks |
| Firewall validation | Hardened (P1) | Hostname/CIDR/loopback/ROE denial tests |
| CI | Blocking | Ruff, pytest, Bandit, pip-audit — no silent failure suppression |
| IR case store | Improved (P2) | Path-safe IDs, tenant filter, atomic write, transitions |
| Tenant isolation | Partial | Env-scoped paths + case filter; claim full isolation only after more cross-tenant API tests |
| SOAR / playbooks | Present | Schema and auth still need continuous hardening |
| SIEM / SOC API | Present | Treat as optional; validate auth on ingest |
| Docs / version | Reconciling | Prefer CHANGELOG + this file over older score tables |
| Isolated VM soak | **Required** | See `docs/PILOT_SOAK.md` — not done by unit tests |
| Legal / ROE / E&O | **Required** | See `docs/LEGAL_GATE.md` |

## Verify locally

```bash
bash scripts/quality_check.sh
python3 -m pytest tests/unit/ -q
bash scripts/pilot_vm_preflight.sh   # on real VM
```

## Do not claim

- "Production-ready live containment" without soak + legal gate
- "Fully automatic defense" — response is rules-driven and gated
- "Multi-tenant isolation complete" until cross-tenant denial tests cover all APIs

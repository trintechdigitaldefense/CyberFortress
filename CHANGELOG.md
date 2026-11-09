# Changelog

## [Unreleased] — hardening branch

### R2 — Installation and runtime reliability
- Isolated pinned dependencies in a repository-local Python virtual environment.
- Added fast-forward-only upgrade with dirty-tree/divergence refusal and source rollback reference.
- Hardened process lifecycle regression, safe environment parsing, and dedicated least-privilege systemd services with bounded resources.

### R3 — Tenant and API security
- Made SOC RBAC fail closed; separated SOC API credentials from dashboard credentials.
- Enforced tenant isolation at agent, dashboard, SOC API, case-store and SIEM boundaries; shared-process multi-tenant mode is disabled.
- Added request rate limits, body/batch/field bounds, tenant path validation and security regression coverage.


## [v0.5.7] — 2026-10-22

### systemd 24/7 + client pack + legal gate
- Full agent roster in `cyberfortress.target` (IR, SOC, intel, auto-defense, …)
- Hardened agent unit defaults; safer install script (`--enable` / `--status` / `--uninstall`)
- `scripts/select_rule_pack.sh` + expanded `docs/RULE_PACKS.md`
- `docs/LEGAL_GATE.md` — attorney review + E&O checklist before live containment
- `pilot_signoff.example.json` — legal gate fields + rule_pack

## [v0.5.6] — 2026-10-22

### Dashboard wiring + client clarity
- WhatsApp webhook + SOC API continuous heartbeats
- agent_status in /api/status with up/stale/down roster
- Live detections + Agents online KPIs

## [v0.5.5] — 2026-10-22

### Client dashboard live monitoring

## [v0.5.4] — 2026-10-22

### Dashboard Tier-2 UI + rule-pack templates

## [v0.5.3] — 2026-10-21

### Tier-2 strengthen

## [v0.1.0] — 2026-10-09

- Initial pilot MVP

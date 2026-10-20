# Changelog

## [v0.3.0-pilot] — 2026-10-19

### Roadmap sprint (detection + cohesion)
- **Real threat hunting loop** — agents pull telemetry each cycle, fuse, audit, optional auto-respond (still dry-run by default)
- **Rule pack v1** — `config/rule_packs/default.yaml` (5 rules) with `pack_id` / `rule_id` on detections
- **Telemetry file archive** — consumed JSON moved to `processed/` (quarantine on bad JSON)
- **Detection audit entries** — every fused event written to hash-chained CMA log
- **Firewall honesty** — `UNAVAILABLE` when host denies netfilter (Permission denied / CAP_NET_ADMIN)
- **Docker parity** — compose runs threat, fusion, firewall (`cap_add: NET_ADMIN`), daily_report, dashboard, health
- **Tests** — rule pack unit tests, firewall status, integration alert→audit chain

### Safety unchanged
- `CF_CONTAINMENT_LIVE=false` default · ROE / breaker / watchdog / WhatsApp nonce controls intact
- No AI/ML claims

## [v0.2.0] — 2026-10-10

### Brief 1–2
- Hardening, audit chain, pytest suite, CI, WhatsApp Tier 2 nonce

## [v0.1.0] — 2026-10-09

- Initial pilot MVP

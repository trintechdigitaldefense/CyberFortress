# CAPABILITIES_VERIFIED — v0.3.0-pilot

**Date:** 2026-10-19
**Repo:** github.com/trintechdigitaldefense/CyberFortress

| Area | Status | Notes |
|------|--------|-------|
| Safety defaults (dry-run, breaker, ROE) | DONE | Unchanged |
| Audit chain | DONE | Detections now append chained entries |
| Threat + fusion loop | DONE | File drops + optional APIs; archive after read |
| Rule packs v1 | DONE | `config/rule_packs/default.yaml` |
| Firewall agent + status | DONE | UNAVAILABLE on permission denied |
| Daily WhatsApp report | DONE | Agent + REPORT_TO |
| Docker parity | DONE | firewall, daily_report, threat command |
| Evidence packs | DONE | Prior release |
| Unit + integration tests | DONE | Rules, firewall, alert→audit |
| Live Meta WhatsApp credentials | HUMAN | Operator provides token |
| Live iptables on restricted hosts | HOST | Needs CAP_NET_ADMIN / real VM |
| Multi-tenant | PENDING | Later |
| Monthly executive PDF reports | PENDING | Later |

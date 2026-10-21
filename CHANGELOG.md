# Changelog

## [v0.3.7] — 2026-10-21

### Strengthen all agents
- Shared `core/agent_runtime.py` — heartbeats, exponential backoff on errors
- Compliance verifies audit chain every cycle
- Firewall re-asserts CF_BLOCK + richer heartbeat meta
- Threat + fusion agents use runtime; report high/critical counts
- Weekly evidence stamps last run; safer skip-on-start
- Health endpoint returns agents, watchdog, monitoring, firewall, audit integrity
- WhatsApp webhook: heartbeats + SO_REUSEADDR threaded server
- Daily report includes monitoring metrics line

## [v0.3.6] — 2026-10-21

### Strengthened monitoring
- Host log/resource adapters, metrics, rule pack v1.1, 30s intervals

## [v0.3.5] — 2026-10-21

### First pilot path
- FIRST_PILOT.md, operator_drill, ROE separate channels

## [v0.3.0-pilot] — 2026-10-19

- Pilot MVP hardening

## [v0.1.0] — 2026-10-09

- Initial pilot MVP

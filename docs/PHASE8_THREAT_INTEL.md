# Phase 8 — Continuous monitoring & threat intelligence

## Goals

- Keep **local IOC feeds** current (file + optional HTTPS URL)
- **Enrich** telemetry with TI hits (does **not** auto-contain)
- Report **collector health** (pids, heartbeats, telemetry freshness)

## Local feeds

Put files under `config/threat_intel/`:

```
203.0.113.50|80|lab,scanner
evil.example.com|75|c2
{"value":"deadbeef...","type":"hash","confidence":90,"tags":["malware"]}
```

## Agents / APIs

| Piece | Role |
|-------|------|
| `agents/threat_intel_agent.py` | Periodic load + URL refresh + monitoring snapshot |
| `core/soc/threat_intel.py` | Match / enrich / status |
| `core/continuous_monitoring.py` | Agents, heartbeats, telemetry staleness |
| Fusion pipeline | `enrich_event` after schema normalize |

## Env

| Variable | Default | Meaning |
|----------|---------|--------|
| `CF_TI_DIR` | `./config/threat_intel` | Feed directory |
| `CF_TI_URL` | empty | Optional HTTPS feed |
| `CF_TI_ALLOW_HTTP` | false | Allow plain HTTP feeds |
| `CF_TI_INTERVAL` | 3600 | Agent cycle seconds |
| `CF_HB_STALE_S` | 180 | Heartbeat stale threshold |

## Safety

TI matches are **signals only**. Containment still requires ROE, live mode, and Tier rules.

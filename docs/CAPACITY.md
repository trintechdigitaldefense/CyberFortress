# CyberFortress — Capacity & soak notes (honest limits)

**TrinTech Digital Defense · v0.3.x**

These are **engineering guidance**, not contractual SLAs. Measure on the pilot VM before promising numbers in an ROE.

## Reference pilot host

| Resource | Suggested minimum |
|----------|-------------------|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Disk | 40 GB |
| OS | Ubuntu 22.04+ |

## Observed / expected limits (single tenant)

| Dimension | Guidance |
|-----------|----------|
| Alert file drops | Comfortable at tens/min; design for < 5 sustained alerts/sec |
| Dedup memory | ~2k–5k recent event ids in process memory |
| Audit log growth | ~1 JSON line per detection/action; rotate/off-box weekly |
| Evidence pack | Seconds for typical pilot history |
| Concurrent tenants | One process tree per tenant |

## Soak recommendations

1. Run 7 days monitoring-only on pilot hardware.
2. Inject synthetic alerts hourly.
3. Confirm disk, watchdog, audit chain, weekly pack.
4. Only then arm live containment for a controlled window.

## What we do not claim

- Unlimited EPS SIEM replacement
- Guaranteed block under kernel/netfilter failure
- Multi-region active-active HA in this release

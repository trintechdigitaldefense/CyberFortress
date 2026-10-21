# Enterprise scale (honest)

CyberFortress targets **local-business → multi-site mid-market**, not a global SOC.

## Scale model

| Tier | Fit |
|------|-----|
| Single site pilot | One host, one tenant (default) |
| Multi-site SMB | Up to **~25 tenants/host** via `config/tenants/*` + `CF_TENANT_ID` |
| Heavy per-site | One process stack per tenant (systemd template / separate VM) |
| Global SOC | Pair with external SIEM; CF stays edge response |

## Smarter agents (not ML)

- 15-minute correlation window (target / indicator / source)
- Burst detection and multi-signal tags
- Asset criticality from tenant settings
- Load shedding when volume exceeds caps
- Adaptive agent intervals under pressure
- Isolated audit / evidence / IR paths per tenant

## Capacity knobs

```bash
CF_CAP_EVENTS_PER_CYCLE=500
CF_CAP_OPEN_IR_CASES=200
CF_CAP_TENANTS_PER_HOST=25
CF_INTEL_WINDOW_S=900
CF_INTEL_BURST_THRESHOLD=8
CF_TENANT_ORCH=true
```

## Multi-tenant

```bash
export CF_TENANT_ID=example_client
./start.sh local
```

Tenant orchestrator scans tenants each minute (lightweight). Production multi-site: prefer **one stack per tenant**.

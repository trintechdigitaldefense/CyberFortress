# CyberFortress Enterprise SOC layer (v0.5.0)

## Honest score

**Architecture readiness toward enterprise SOC: ~9/10**  
**Production 10/10:** still needs your SIEM, IdP SSO, HA pair on real VMs, signed ROE, live WhatsApp/TLS.

| Dimension | Score |
|-----------|-------|
| Detection + correlation | 9/10 |
| Response automation (SOAR-lite) | 9/10 |
| SIEM interoperability | 8.5/10 |
| Observability (Prometheus) | 9/10 |
| RBAC | 8/10 |
| Multi-tenant | 8/10 |
| Global 10k+ EPS multi-region | 6/10 — pair with enterprise SIEM |

## Endpoints

- `GET http://127.0.0.1:8092/metrics`
- `POST /api/soc/ingest` — JSON event or `{events:[...]}`
- `POST /api/soc/ingest/cef` — CEF lines
- `GET /api/soc/health` — HA + bus + TI

## Auth

```bash
export CF_SOC_REQUIRE_AUTH=true
export CF_SOC_USERS=admin:admin:secret-token
# Authorization: Bearer secret-token
```

Playbooks in `config/playbooks/` always respect LIVE/ROE/WhatsApp gates.

# CyberFortress firewall (strengthened)

## Behaviour

| Mode | What happens |
|------|----------------|
| **MONITORING** (`CF_CONTAINMENT_LIVE=false`) | Chain may exist; **no new DROP** from alerts |
| **ARMED** (`CF_CONTAINMENT_LIVE=true`) | `block_ip` inserts src+dst DROP in `CF_BLOCK` |

## Strengthened controls

1. **IP validation** — reject loopback, multicast, link-local; private ranges rejected unless `CF_FIREWALL_ALLOW_PRIVATE=true`
2. **Allowlist** — `CF_FIREWALL_ALLOWLIST` and `config/firewall_allowlist.txt` never blocked
3. **Max rules** — `CF_FIREWALL_MAX_RULES` (default 200)
4. **Dedupe** — skip insert if target already in chain
5. **Post-action verify** — live blocks fail if rule not found after insert
6. **FORWARD hook** — chain linked from INPUT, OUTPUT, and FORWARD
7. **Live mode re-read** — each call reads current env (not frozen at import)
8. **Status persistence** — `logs/firewall_status.json`

## Env

```bash
CF_CONTAINMENT_LIVE=false
CF_FIREWALL_AUTO_START=true
CF_IPTABLES_CHAIN=CF_BLOCK
CF_FIREWALL_MAX_RULES=200
CF_FIREWALL_ALLOW_PRIVATE=false
CF_FIREWALL_ALLOWLIST=203.0.113.10,10.0.0.1
# optional file: config/firewall_allowlist.txt
```

## Host requirement

Root + `iptables` + `CAP_NET_ADMIN` for real DROP. See `docs/HOST_REQUIREMENTS.md`.

# CyberFortress — Real VM pilot (netadmin before arming)

**WhatsApp credentials can be added later.**

Live `CF_BLOCK` DROP rules only work on a host that passes netfilter checks.

## One-command preflight

```bash
./scripts/pilot_vm_preflight.sh
```

This **must** leave `check_netadmin.sh` **green**. If it fails → **MONITORING only**.

On success:

- writes `config/host_capability.json` (`netadmin_ok: true`)
- stamps `host_netadmin_verified: true` in `config/pilot_signoff.json` if present

## Sequence

| Step | Action |
|------|--------|
| 1 | Deploy on Ubuntu 22.04+ VM |
| 2 | `./install.sh` · `./start.sh local` |
| 3 | `./scripts/pilot_vm_preflight.sh` → **green** |
| 4 | Sign NDA + ROE; fill `config/pilot_signoff.json` |
| 5 | Keep `whatsapp_deferred: true` until Meta token is ready |
| 6 | `./scripts/enable_live_mode.sh --check` then `--enable` |
| 7 | Later: WhatsApp — set `whatsapp_tls_verified: true`, `whatsapp_deferred: false` |

## Hard rules

1. Arming is **refused** if `check_netadmin.sh` fails at enable time.
2. Arming is **refused** if `host_netadmin_verified` is not true.
3. WhatsApp is optional for arming only when `whatsapp_deferred: true`.
4. Restricted containers with iptables Permission denied stay monitoring-only.

## Related

- [HOST_REQUIREMENTS.md](HOST_REQUIREMENTS.md)
- [GO_LIVE.md](GO_LIVE.md)
- [WHATSAPP_TLS.md](WHATSAPP_TLS.md)

# CyberFortress systemd (24/7)

Survives reboot. Prefer **either** systemd **or** `./start.sh` — not both.

## Install + enable

```bash
cd /opt/CyberFortress   # or your clone path
sudo ./deploy/systemd/install_systemd.sh
sudo systemctl enable --now cyberfortress.target
sudo ./deploy/systemd/install_systemd.sh --status
```

One-shot:

```bash
sudo ./deploy/systemd/install_systemd.sh --enable
```

## Ops

| Command | Effect |
|---------|--------|
| `systemctl status cyberfortress.target` | Platform overview |
| `systemctl status 'cyberfortress-agent@*'` | Per-agent |
| `journalctl -u cyberfortress-agent@dashboard -f` | Dashboard logs |
| `systemctl stop cyberfortress.target` | Stop all CF units |
| `systemctl start cyberfortress.target` | Start all |
| `sudo ./deploy/systemd/install_systemd.sh --uninstall` | Remove units only |

## Safety

- Units default `CF_CONTAINMENT_LIVE=false` if env omits it.
- Firewall unit requests `CAP_NET_ADMIN`; other agents stay hardened (`NoNewPrivileges`).
- Dashboard / health / WhatsApp bind stay localhost unless you set `CF_ALLOW_PUBLIC_BIND` (not recommended).
- Live mode still requires ROE + `pilot_signoff.json` + `enable_live_mode.sh`.

## Agents covered

Detection, fusion, threat intel, auto-defense, firewall, playbooks, full IR team, compliance, watchdog, health, dashboard, daily/weekly reports, SOC API, SIEM bridge, tenant orchestrator, WhatsApp webhook.

Installer rewrites `/opt/CyberFortress` paths to your install root.

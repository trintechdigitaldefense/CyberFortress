# CyberFortress systemd (optional 24/7)

```bash
cd /opt/CyberFortress
sudo ./deploy/systemd/install_systemd.sh
sudo systemctl enable --now cyberfortress.target
sudo systemctl status cyberfortress.target
```

Stop: `sudo systemctl stop cyberfortress.target`

Defaults stay dry-run. Firewall unit requests CAP_NET_ADMIN. Dashboard/health stay localhost.

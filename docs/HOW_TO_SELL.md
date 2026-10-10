# CyberFortress — How to Sell

**TrinTech Digital Defense positioning**

> **Pricing:** not published yet. Platform is still being built and improved.  
> Stay tuned — commercial numbers will be added when ready.

---

## One-liner

> CyberFortress watches your network, contains threats fast, and only takes big steps after your team approves on WhatsApp — with a full audit trail under Trinidad & Tobago law.

---

## Who buys it

- SMBs and mid-market in T&T / Caribbean with limited SOC staff
- Clients who already use (or will use) TrinTech Sentinel / Mirage
- Organisations that need **defensible** automated response, not just alerts

---

## Pain → pitch

| Pain | Pitch |
|------|--------|
| Alerts with no action | Automated Tier 1 response in minutes |
| Fear of runaway automation | Tier 2 needs WhatsApp `APPROVE <code>`; ROE allow-list |
| Audit / regulator questions | Every action mapped to TT Computer Misuse Act + Evidence Pack |
| Weekend / after-hours gaps | 24/7 agents + watchdog fail-closed |

---

## Packages (no prices yet)

### 1) Pilot (recommended first engagement)
- 2 weeks **dry-run** on client scope
- **NDA + ROE** + named WhatsApp admins
- Weekly evidence pack
- Optional week of **gated live** for listed actions only
- Requires completed `config/pilot_signoff.json` before any live mode

### 2) Managed CyberFortress
- Ongoing monitoring + operator cover
- Live mode under ROE
- Monthly evidence + backup

### 3) Add-on to existing TrinTech work
- Bolt onto vulnerability assessment / network audit clients who need response capability

Commercial terms: **TBD** — do not quote a fee from this repo until TrinTech publishes pricing.

---

## What to say about safety

- Default is **dry-run** — nothing hits the firewall until sign-off
- High-impact actions need WhatsApp **`APPROVE <nonce>`** from a registered admin
- Unknown numbers and bad codes are denied and logged
- Only actions on the **ROE list** can run
- Live mode blocked until **NDA + ROE + pilot_signoff.json** are complete
- Emergency stop: disable live mode + trip circuit breaker
- Full **evidence pack** for the client after incidents

---

## What not to promise

- “Fully autonomous, no humans”
- “AI / machine learning” (this MVP is rules-driven automation)
- “Replaces your entire IT team”
- “Works with zero ROE”
- Guaranteed prevention of all breaches
- Any fixed price from this repository

---

## Demo flow (30 minutes)

1. `./install.sh` && `./start.sh` — dashboard dry-run mode  
2. Inject sample Sentinel/Mirage alert → escalation  
3. Tier 1 `block_ip` dry-run + CMA log line  
4. Show Evidence Pack ZIP  
5. Tier 2 isolate → WhatsApp `APPROVE <nonce>` (or mock path)  
6. Show ROE / NDA templates + pilot checklist + go-live gate  

---

## Leave-behind

- Overview PDF / cheatsheet  
- Pilot proposal (scope + ROE summary — **no price until published**)  
- Sanitized sample evidence report  

---

*Defend. Detect. Dominate.*

# IR Response Team agents

CyberFortress runs a **four-agent response team** on top of monitoring:

| Agent | Role | Module |
|-------|------|--------|
| **Detect** | Open cases from HIGH/CRITICAL audit detections | `agents.ir_detect_agent` |
| **Investigate** | Structured findings (rules-driven) | `agents.ir_investigate_agent` |
| **Respond** | ROE-safe playbooks via autonomy (dry-run unless armed) | `agents.ir_respond_agent` |
| **Report** | Markdown incident reports under `evidence/ir_reports/` | `agents.ir_report_agent` |

## Safety

- Same gates: **LIVE default off**, ROE allow-list, WhatsApp Tier‑2, circuit breaker.
- Respond agent calls `execute_with_autonomy` — no bypass of approvals.
- Cases: `logs/ir_cases/`.

## API

`GET /api/ir/cases` on the dashboard port.

## Env

```bash
CF_IR_DETECT_INTERVAL=45
CF_IR_INVESTIGATE_INTERVAL=40
CF_IR_RESPOND_INTERVAL=50
CF_IR_REPORT_INTERVAL=60
CF_IR_AUTO_RESPOND=true
CF_IR_NOTIFY_REPORTS=true
```

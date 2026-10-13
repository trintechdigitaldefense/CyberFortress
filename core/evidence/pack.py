#!/usr/bin/env python3
"""CyberFortress Evidence Pack Generator - client-ready MD/HTML reports."""

from __future__ import annotations

import json
import hashlib
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cf_evidence")

EVIDENCE_ROOT = Path(os.getenv("CF_EVIDENCE_DIR", "./evidence"))
AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))


def _esc(val: Any) -> str:
    return (
        str(val if val is not None else "")
        .replace("&", "&")
        .replace("<", "<")
        .replace(">", ">")
        .replace('"', """)
    )


class EvidencePack:
    def __init__(self, client_name: str = "Client", engagement_id: Optional[str] = None):
        self.client_name = client_name
        self.engagement_id = engagement_id or datetime.now(timezone.utc).strftime("ENG-%Y%m%d-%H%M")
        self.created_at = datetime.now(timezone.utc)
        self.actions: List[Dict[str, Any]] = []
        self.pack_dir: Optional[Path] = None
        self.meta: Dict[str, Any] = {}

    def load_from_audit_log(self, audit_path: Optional[str] = None) -> int:
        path = Path(audit_path) if audit_path else AUDIT_PATH
        if not path.exists():
            logger.warning("No audit log at %s", path)
            return 0
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    self.actions.append(json.loads(line))
                    count += 1
                except json.JSONDecodeError:
                    continue
        logger.info("Loaded %s audit entries", count)
        return count

    def _platform_context(self) -> Dict[str, Any]:
        live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
        ctx: Dict[str, Any] = {
            "mode": "LIVE PROTECTION" if live else "PRACTICE MODE (dry-run)",
            "containment_live": live,
            "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
            "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        }
        try:
            from core.circuit_breaker import breaker
            ctx["circuit_breaker"] = breaker.status()
        except Exception:
            ctx["circuit_breaker"] = {"state": "UNKNOWN"}
        try:
            from core.roe import roe_status
            ctx["roe"] = roe_status()
        except Exception:
            ctx["roe"] = {"signoff_present": False, "source": "unknown"}
        try:
            from core.audit_chain import verify_chain
            ok, idx, msg = verify_chain(AUDIT_PATH)
            ctx["audit_integrity"] = {"ok": ok, "message": msg, "broken_index": idx}
        except Exception as e:
            ctx["audit_integrity"] = {"ok": False, "message": str(e), "broken_index": None}
        return ctx

    def _generate_summary(self) -> Dict[str, Any]:
        by_severity: Dict[str, int] = {}
        by_action: Dict[str, int] = {}
        approved = held = 0
        for a in self.actions:
            sev = a.get("severity", "INFO")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            act = a.get("action", "unknown")
            by_action[act] = by_action.get(act, 0) + 1
            just = str(a.get("legislative_justification", ""))
            if "APPROVED" in just or "FORCE" in just:
                approved += 1
            if "HELD" in just:
                held += 1
        ctx = self._platform_context()
        return {
            "client": self.client_name,
            "engagement_id": self.engagement_id,
            "generated_at": self.created_at.isoformat(),
            "total_actions": len(self.actions),
            "approved_or_forced": approved,
            "held": held,
            "by_severity": by_severity,
            "by_action": by_action,
            **ctx,
        }

    def _write_human_report(self, path: Path) -> None:
        s = self._generate_summary()
        ai = s.get("audit_integrity") or {}
        roe = s.get("roe") or {}
        cb = s.get("circuit_breaker") or {}
        lines = [
            "# CyberFortress - Evidence Report",
            "",
            "**Client:** {}  ".format(self.client_name),
            "**Engagement ID:** {}  ".format(self.engagement_id),
            "**Generated:** {}  ".format(self.created_at.strftime("%Y-%m-%d %H:%M UTC")),
            "**Prepared by:** TrinTech Digital Defense (Trinidad & Tobago)",
            "",
            "---",
            "",
            "## 1. Platform status at time of report",
            "",
            "| Item | Value |",
            "|------|-------|",
            "| Operating mode | {} |".format(s.get("mode")),
            "| Circuit breaker | {} |".format(cb.get("state", "-")),
            "| ROE source | {} |".format(roe.get("source", "-")),
            "| Pilot sign-off on file | {} |".format("Yes" if roe.get("signoff_present") else "No"),
            "| Audit chain integrity | {} - {} |".format(
                "OK" if ai.get("ok") else "CHECK NEEDED", ai.get("message", "")
            ),
            "| WhatsApp approvals | {} |".format(
                "Enabled" if s.get("whatsapp_enabled") else "Not connected"
            ),
            "",
            "## 2. Executive summary",
            "",
            "This report lists protective actions recorded by CyberFortress for **{}**. ".format(
                self.client_name
            )
            + "Each action is rules-driven and mapped to the Trinidad and Tobago Computer Misuse Act "
            "for authorized defensive use.",
            "",
            "- **Total actions recorded:** {}".format(s["total_actions"]),
            "- **Approved or force-executed:** {}".format(s["approved_or_forced"]),
            "- **Held pending human approval:** {}".format(s["held"]),
            "",
        ]
        if s["total_actions"] == 0:
            lines += [
                "> No protective actions were in the audit log when this pack was generated. "
                "That is normal on a fresh install or before the first detection cycle.",
                "",
            ]
        lines += ["### Severity", ""]
        if s["by_severity"]:
            for sev, count in sorted(s["by_severity"].items()):
                lines.append("- **{}:** {}".format(sev, count))
        else:
            lines.append("- None")
        lines += ["", "### Action types", ""]
        if s["by_action"]:
            for act, count in sorted(s["by_action"].items(), key=lambda x: (-x[1], x[0])):
                lines.append("- `{}`: {}".format(act, count))
        else:
            lines.append("- None")
        lines += [
            "",
            "---",
            "",
            "## 3. Detailed action log",
            "",
            "Times are UTC. Justifications are the legislative notes written into the audit trail.",
            "",
        ]
        if not self.actions:
            lines.append("_No actions to list._")
            lines.append("")
        for i, a in enumerate(self.actions, 1):
            lines += [
                "### {}. `{}` -> `{}`".format(i, a.get("action", "unknown"), a.get("target", "unknown")),
                "",
                "| Field | Value |",
                "|-------|-------|",
                "| Time | {} |".format(a.get("timestamp", "N/A")),
                "| Severity | {} |".format(a.get("severity", "N/A")),
                "| Entry hash | `{}` |".format((a.get("entry_hash") or "-")[:16]),
                "| Justification | {} |".format(a.get("legislative_justification", "N/A")),
                "",
            ]
        lines += [
            "---",
            "",
            "## 4. Integrity",
            "",
            "- `MANIFEST.sha256` lists SHA-256 digests of every file in this pack.",
            "- `03_Raw_CMA_Audit.jsonl` is the append-only audit chain (when present).",
            "- Re-verify on the host: `python3 scripts/verify_audit_chain.py`",
            "",
            "---",
            "",
            "*Authorized defensive use only. Not for offensive activity.*",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_html_report(self, path: Path) -> None:
        s = self._generate_summary()
        ai = s.get("audit_integrity") or {}
        roe = s.get("roe") or {}
        cb = s.get("circuit_breaker") or {}
        rows = []
        for a in self.actions:
            rows.append(
                "<tr><td>{}</td><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    _esc(a.get("timestamp", "")),
                    _esc(a.get("action", "")),
                    _esc(a.get("target", "")),
                    _esc(a.get("severity", "")),
                    _esc(a.get("legislative_justification", "")),
                )
            )
        table = "\n".join(rows) if rows else '<tr><td colspan="5">No actions recorded</td></tr>'
        css = (
            "body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;"
            "padding:0 1rem;color:#0f172a;line-height:1.5}"
            "h1{font-size:1.4rem}h2{font-size:1.1rem;margin-top:1.5rem;"
            "border-bottom:1px solid #e2e8f0;padding-bottom:.3rem}"
            "table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.75rem 0}"
            "th,td{border:1px solid #e2e8f0;padding:.45rem .6rem;text-align:left;vertical-align:top}"
            "th{background:#f1f5f9}.meta{color:#475569;font-size:.9rem}"
            ".badge{display:inline-block;padding:.15rem .5rem;border-radius:6px;"
            "background:#e0f2fe;font-size:.8rem}"
            "footer{margin-top:2rem;color:#64748b;font-size:.8rem}"
        )
        html = (
            "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            "<title>CyberFortress Evidence - {}</title><style>{}</style></head><body>"
            "<h1>CyberFortress Evidence Report</h1>"
            "<p class=\"meta\"><strong>Client:</strong> {} - "
            "<strong>Engagement:</strong> {} - "
            "<strong>Generated:</strong> {}<br>"
            "TrinTech Digital Defense - Trinidad & Tobago</p>"
            "<h2>Platform status</h2><table>"
            "<tr><th>Item</th><th>Value</th></tr>"
            "<tr><td>Mode</td><td><span class=\"badge\">{}</span></td></tr>"
            "<tr><td>Circuit breaker</td><td>{}</td></tr>"
            "<tr><td>ROE</td><td>{} (sign-off: {})</td></tr>"
            "<tr><td>Audit integrity</td><td>{} - {}</td></tr></table>"
            "<h2>Executive summary</h2><ul>"
            "<li>Total actions: <strong>{}</strong></li>"
            "<li>Approved / forced: <strong>{}</strong></li>"
            "<li>Held for approval: <strong>{}</strong></li></ul>"
            "<p>Rules-driven protective actions mapped to the Computer Misuse Act "
            "for authorized defensive use.</p>"
            "<h2>Action log</h2><table>"
            "<thead><tr><th>Time (UTC)</th><th>Action</th><th>Target</th>"
            "<th>Severity</th><th>Justification</th></tr></thead>"
            "<tbody>{}</tbody></table>"
            "<footer>Integrity: see MANIFEST.sha256 and 03_Raw_CMA_Audit.jsonl. "
            "Verify with scripts/verify_audit_chain.py.<br>"
            "Authorized defensive use only.</footer></body></html>"
        ).format(
            _esc(self.client_name),
            css,
            _esc(self.client_name),
            _esc(self.engagement_id),
            self.created_at.strftime("%Y-%m-%d %H:%M UTC"),
            _esc(s.get("mode")),
            _esc(cb.get("state", "-")),
            _esc(roe.get("source", "-")),
            "yes" if roe.get("signoff_present") else "no",
            "OK" if ai.get("ok") else "CHECK",
            _esc(ai.get("message", "")),
            s["total_actions"],
            s["approved_or_forced"],
            s["held"],
            table,
        )
        path.write_text(html, encoding="utf-8")

    def build(self, output_root: Optional[str] = None) -> Path:
        root = Path(output_root) if output_root else EVIDENCE_ROOT
        root.mkdir(parents=True, exist_ok=True)
        stamp = self.created_at.strftime("%Y%m%d_%H%M%S")
        self.pack_dir = root / "{}_{}".format(self.engagement_id, stamp)
        self.pack_dir.mkdir(parents=True, exist_ok=True)

        self._write_human_report(self.pack_dir / "01_Executive_Report.md")
        self._write_html_report(self.pack_dir / "01_Executive_Report.html")

        summary = self._generate_summary()
        self.meta = summary
        with open(self.pack_dir / "02_Full_Audit.json", "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "actions": self.actions}, f, indent=2, default=str)

        if AUDIT_PATH.exists():
            shutil.copy(AUDIT_PATH, self.pack_dir / "03_Raw_CMA_Audit.jsonl")

        manifest = {}
        for file in sorted(self.pack_dir.iterdir()):
            if file.is_file() and file.name != "MANIFEST.sha256":
                manifest[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
        with open(self.pack_dir / "MANIFEST.sha256", "w", encoding="utf-8") as f:
            for name, digest in manifest.items():
                f.write("{}  {}\n".format(digest, name))

        logger.info("Evidence pack created at %s", self.pack_dir)
        return self.pack_dir

    def zip(self) -> Path:
        if not self.pack_dir or not self.pack_dir.exists():
            raise RuntimeError("Call build() first")
        zip_path = shutil.make_archive(str(self.pack_dir), "zip", root_dir=self.pack_dir)
        logger.info("Evidence ZIP created: %s", zip_path)
        return Path(zip_path)


def list_evidence_packs(limit: int = 10) -> List[Dict[str, Any]]:
    root = EVIDENCE_ROOT
    if not root.exists():
        return []
    zips = sorted(root.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for z in zips[:limit]:
        out.append({
            "name": z.name,
            "path": str(z),
            "size_bytes": z.stat().st_size,
            "modified": datetime.fromtimestamp(z.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return out


def generate_evidence_pack(
    client_name: str = "Client",
    engagement_id: Optional[str] = None,
    create_zip: bool = True,
) -> Path:
    pack = EvidencePack(client_name=client_name, engagement_id=engagement_id)
    pack.load_from_audit_log()
    pack.build()
    if create_zip:
        return pack.zip()
    return pack.pack_dir  # type: ignore[return-value]


def generate_evidence_pack_with_meta(
    client_name: str = "Client",
    create_zip: bool = True,
) -> Dict[str, Any]:
    pack = EvidencePack(client_name=client_name)
    n = pack.load_from_audit_log()
    folder = pack.build()
    zip_path = pack.zip() if create_zip else None
    return {
        "ok": True,
        "actions_loaded": n,
        "folder": str(folder),
        "path": str(zip_path) if zip_path else str(folder),
        "zip": str(zip_path) if zip_path else None,
        "summary": pack.meta,
        "files": sorted(p.name for p in folder.iterdir() if p.is_file()),
    }

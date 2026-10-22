"""CyberFortress dashboard HTML UI."""
from pathlib import Path

_UI_PATH = Path(__file__).resolve().parent / "static" / "dashboard.html"


def get_dashboard_html() -> str:
    return _UI_PATH.read_text(encoding="utf-8")


# Back-compat for `from agents.dashboard_ui import DASHBOARD_HTML`
try:
    DASHBOARD_HTML = get_dashboard_html()
except Exception:
    DASHBOARD_HTML = "<html><body>Dashboard UI missing</body></html>"

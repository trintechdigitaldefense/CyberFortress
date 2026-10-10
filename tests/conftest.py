import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("CF_CONTAINMENT_LIVE", "false")
os.environ.setdefault("CF_ALLOW_FORCE", "false")
os.environ.setdefault("CF_WHATSAPP_ENABLED", "false")
os.environ.setdefault("CF_WHATSAPP_MOCK", "true")

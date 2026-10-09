#!/usr/bin/env python3
"""
CyberFortress Direct API Connectors for Sentinel & Mirage

These connectors pull live alerts over HTTP instead of relying solely
on file drops. They fall back gracefully if the remote service is
unreachable.

Environment variables:
  CF_SENTINEL_API_URL=http://sentinel-host:port/api/alerts
  CF_SENTINEL_API_KEY=...
  CF_MIRAGE_API_URL=http://mirage-host:port/api/events
  CF_MIRAGE_API_KEY=...
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import requests

from core.telemetry.adapters import BaseAdapter

logger = logging.getLogger("cf_telemetry.api")


class SentinelAPIConnector(BaseAdapter):
    """Live pull from Sentinel HTTP API."""

    source_name = "sentinel_api"

    def __init__(self):
        self.base_url = os.getenv("CF_SENTINEL_API_URL", "").rstrip("/")
        self.api_key = os.getenv("CF_SENTINEL_API_KEY", "")
        self.timeout = int(os.getenv("CF_SENTINEL_TIMEOUT", "15"))

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if not self.base_url:
            logger.debug("CF_SENTINEL_API_URL not set — skipping Sentinel API connector")
            return []

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        params = {}
        if since:
            params["since"] = since.isoformat()

        try:
            r = requests.get(
                f"{self.base_url}/alerts" if not self.base_url.endswith("/alerts") else self.base_url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()

            raw_list = data if isinstance(data, list) else data.get("alerts", data.get("events", []))
            events = []
            for item in raw_list:
                events.append(self.normalize(item))
            logger.info(f"Sentinel API returned {len(events)} events")
            return events

        except requests.exceptions.RequestException as e:
            logger.warning(f"Sentinel API unreachable: {e}")
            return []
        except Exception as e:
            logger.exception(f"Sentinel API connector error: {e}")
            return []


class MirageAPIConnector(BaseAdapter):
    """Live pull from Mirage deception platform HTTP API."""

    source_name = "mirage_api"

    def __init__(self):
        self.base_url = os.getenv("CF_MIRAGE_API_URL", "").rstrip("/")
        self.api_key = os.getenv("CF_MIRAGE_API_KEY", "")
        self.timeout = int(os.getenv("CF_MIRAGE_TIMEOUT", "15"))

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if not self.base_url:
            logger.debug("CF_MIRAGE_API_URL not set — skipping Mirage API connector")
            return []

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        params = {}
        if since:
            params["since"] = since.isoformat()

        try:
            r = requests.get(
                f"{self.base_url}/events" if not self.base_url.endswith("/events") else self.base_url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()

            raw_list = data if isinstance(data, list) else data.get("events", data.get("alerts", []))
            events = []
            for item in raw_list:
                item.setdefault("indicator", "decoy_trigger")
                events.append(self.normalize(item))
            logger.info(f"Mirage API returned {len(events)} events")
            return events

        except requests.exceptions.RequestException as e:
            logger.warning(f"Mirage API unreachable: {e}")
            return []
        except Exception as e:
            logger.exception(f"Mirage API connector error: {e}")
            return []

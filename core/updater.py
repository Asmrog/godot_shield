"""
GitHub Releases update checker for Godot Shield.

Uses only the Python standard library so the frozen EXE needs no extra
dependencies. Network/parse failures are returned as a structured result
instead of being raised, so a failed check can never take down the GUI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.request import Request, urlopen

from .i18n import APP_VERSION

RELEASES_API_URL = "https://api.github.com/repos/Asmrog/godot_shield/releases/latest"
FALLBACK_RELEASE_URL = "https://github.com/Asmrog/godot_shield/releases/latest"
REQUEST_TIMEOUT = 10


@dataclass(frozen=True)
class UpdateCheckResult:
    """Outcome of a single update check."""

    available: bool = False
    latest_version: str = ""
    release_url: str = ""
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def _version_tuple(version: str) -> tuple[int, int, int]:
    """Turn 'v1.2.1' or '1.3.0-beta' into a comparable (1, 2, 1) tuple."""
    cleaned = str(version or "").strip().lstrip("vV")
    cleaned = re.split(r"[-+]", cleaned, maxsplit=1)[0]
    parts: list[int] = []
    for piece in cleaned.split(".")[:3]:
        match = re.match(r"\d+", piece)
        parts.append(int(match.group()) if match else 0)
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def check_for_updates(current_version: str = APP_VERSION) -> UpdateCheckResult:
    """Query the latest GitHub release and compare it with current_version.

    Args:
        current_version: Version reported by the app (defaults to APP_VERSION).

    Returns:
        UpdateCheckResult with ``available`` set when a newer release exists.
        On any network or parsing problem, ``error`` is set instead.
    """
    try:
        request = Request(
            RELEASES_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                # GitHub rejects requests without a User-Agent.
                "User-Agent": "GodotShield-UpdateChecker",
            },
        )
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError("Unexpected response from the releases API")

        latest_version = str(payload.get("tag_name") or "").strip()
        if not latest_version:
            raise ValueError("Latest release has no tag_name")

        release_url = str(payload.get("html_url") or "").strip() or FALLBACK_RELEASE_URL
        return UpdateCheckResult(
            available=_version_tuple(latest_version) > _version_tuple(current_version),
            latest_version=latest_version,
            release_url=release_url,
        )
    except Exception as exc:  # offline, timeout, bad JSON, API error, ...
        return UpdateCheckResult(error=str(exc) or exc.__class__.__name__)

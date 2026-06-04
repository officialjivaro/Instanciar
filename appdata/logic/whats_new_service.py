# appdata/logic/whats_new_service.py
"""
Load Instanciar's live What's New content from GitHub.

There is intentionally no bundled release-notes fallback. If GitHub cannot be
reached, the app shows a short error panel instead of storing release notes
inside the executable.
"""

from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from PySide6.QtCore import QSettings

from appdata.config.whats_new import (
    GITHUB_RELEASE_NOTES_FOLDER_URL,
    INSTANCIAR_DOWNLOAD_URL,
    WHATS_NEW_RELEASE_NOTES_URL,
    WHATS_NEW_TIMEOUT_SECONDS,
    WHATS_NEW_URL,
)

_SETTINGS_ORG = "Jivaro"
_SETTINGS_APP = "Instanciar"
_LAST_SEEN_KEY = "whats_new/last_seen_content_id"
_UNAVAILABLE_CONTENT_ID = "github-release-notes-unavailable"


@dataclass(frozen=True)
class WhatsNewContent:
    content_id: str
    title: str
    body: str
    source: str
    is_remote: bool
    format: str = "markdown"
    download_url: str = INSTANCIAR_DOWNLOAD_URL
    release_notes_url: str = WHATS_NEW_RELEASE_NOTES_URL


# Section Name | Remote loading
def _fetch_remote_markdown() -> str:
    """Fetch the live GitHub Markdown file configured in whats_new.py."""
    request = urllib.request.Request(
        WHATS_NEW_URL,
        headers={
            "User-Agent": "Instanciar WhatsNew/1.0",
            "Accept": "text/markdown,text/plain,text/html;q=0.9,*/*;q=0.5",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=WHATS_NEW_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read(512_000).decode(charset, errors="replace")


# Section Name | Error content
def _unavailable_markdown(error_message: str = "") -> str:
    detail = ""
    if error_message:
        detail = f"\n\nTechnical detail: `{error_message}`"

    return (
        "# What’s New\n\n"
        "Instanciar could not load the live release notes from GitHub right now.\n\n"
        "There may be a problem reaching GitHub, the release-notes file may not exist yet, "
        "or the network may be blocking access to the site.\n\n"
        f"GitHub release notes folder: {GITHUB_RELEASE_NOTES_FOLDER_URL}\n\n"
        f"Expected raw file: {WHATS_NEW_URL}\n\n"
        f"[Download Instanciar]({INSTANCIAR_DOWNLOAD_URL})"
        f"{detail}\n"
    )


# Section Name | Content parsing
def _extract_content_id(text: str) -> str:
    """
    Extract a content ID from the live Markdown.

    Supported formats near the top of the GitHub file:
        <!-- Content ID: instanciar-v014-2026-06-04 -->

        <!--
        Content ID: instanciar-v014-2026-06-04
        Updated: 2026-06-04
        -->

        Content ID: instanciar-v014-2026-06-04

    Change this ID whenever you want the panel to show again for users.
    """
    # Search line-by-line so a multi-line HTML comment does not accidentally
    # capture Updated/Latest metadata as part of the content ID.
    for raw_line in text.splitlines()[:40]:
        line = raw_line.strip()
        if not line:
            continue

        line = line.removeprefix("<!--").removesuffix("-->").strip()

        match = re.match(
            r"(?:Content\s*ID|Content-ID|content_id)\s*[:=]\s*(.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        value = match.group(1).strip().strip("- ").strip()
        value = value.replace("-->", "").strip()
        if value:
            return value

    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"instanciar-whats-new-{digest}"


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip() or "What’s New in Instanciar"
    return "What’s New in Instanciar"


def _content_format(text: str) -> str:
    sample = text.lstrip().lower()
    if sample.startswith("<!doctype html") or sample.startswith("<html") or "<body" in sample[:500]:
        return "html"
    return "markdown"


# Section Name | Public API
def load_whats_new_content(prefer_remote: bool = True) -> WhatsNewContent:
    """
    Load live GitHub content.

    If GitHub cannot be reached, return an unavailable-message payload instead
    of reading bundled release notes from the app.
    """
    if prefer_remote:
        try:
            remote_body = _fetch_remote_markdown()
            if remote_body.strip():
                return WhatsNewContent(
                    content_id=_extract_content_id(remote_body),
                    title=_extract_title(remote_body),
                    body=remote_body,
                    source=WHATS_NEW_URL,
                    is_remote=True,
                    format=_content_format(remote_body),
                )
        except urllib.error.HTTPError as exc:
            error_message = f"HTTP {exc.code}: {exc.reason}"
        except urllib.error.URLError as exc:
            error_message = str(exc.reason)
        except Exception as exc:
            error_message = str(exc)
    else:
        error_message = "remote loading was disabled"

    body = _unavailable_markdown(error_message)
    return WhatsNewContent(
        content_id=_UNAVAILABLE_CONTENT_ID,
        title="Could Not Load What’s New",
        body=body,
        source=WHATS_NEW_URL,
        is_remote=False,
        format="markdown",
    )


def _settings() -> QSettings:
    return QSettings(_SETTINGS_ORG, _SETTINGS_APP)


def get_last_seen_content_id() -> str:
    return str(_settings().value(_LAST_SEEN_KEY, "") or "")


def has_seen_content(content_id: str) -> bool:
    return bool(content_id) and get_last_seen_content_id() == content_id


def mark_content_seen(content_id: str) -> None:
    if not content_id:
        return
    settings = _settings()
    settings.setValue(_LAST_SEEN_KEY, content_id)
    settings.sync()

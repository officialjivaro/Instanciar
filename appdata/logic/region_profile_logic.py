# appdata/logic/region_profile_logic.py
"""Helpers for resolving Instanciar region profile settings."""

from copy import deepcopy
from typing import Dict, Optional

from appdata.config.constants import LANG_CODE_MAP
from appdata.config.region_profiles import (
    DEFAULT_LEGACY_LAUNCH_MODE,
    DEFAULT_NEW_LAUNCH_MODE,
    LAUNCH_MODE_MAP,
    LAUNCH_MODES,
    REGION_PROFILE_MAP,
    REGION_PROFILES,
)


def region_choices() -> list[tuple[str, str]]:
    """Return display label/key pairs for region dropdowns."""
    return [(profile["label"], profile["key"]) for profile in REGION_PROFILES]


def launch_mode_choices() -> list[tuple[str, str]]:
    """Return display label/key pairs for launch-mode dropdowns."""
    return [(mode["label"], mode["key"]) for mode in LAUNCH_MODES]


def normalize_region_profile_key(value: object) -> str:
    key = str(value or "").strip()
    return key if key in REGION_PROFILE_MAP else ""


def get_region_profile(value: object) -> Optional[Dict]:
    key = normalize_region_profile_key(value)
    if not key:
        return None
    return REGION_PROFILE_MAP.get(key)


def region_profile_label(value: object) -> str:
    profile = get_region_profile(value)
    return profile["label"] if profile else "None"


def normalize_launch_mode(value: object, *, default: str = DEFAULT_LEGACY_LAUNCH_MODE) -> str:
    key = str(value or "").strip().lower()
    if key in LAUNCH_MODE_MAP:
        return key
    return default if default in LAUNCH_MODE_MAP else DEFAULT_LEGACY_LAUNCH_MODE


def launch_mode_label(value: object) -> str:
    key = normalize_launch_mode(value)
    return LAUNCH_MODE_MAP[key]["label"]


def launch_mode_description(value: object) -> str:
    key = normalize_launch_mode(value)
    return LAUNCH_MODE_MAP[key]["description"]


def language_to_code(language: object) -> str:
    text = str(language or "").strip()
    return str(LANG_CODE_MAP.get(text, text)).strip()


def resolved_identity_settings(identity: Optional[Dict], *, default_launch_mode: str = DEFAULT_LEGACY_LAUNCH_MODE) -> Dict:
    """
    Return a copy of identity settings with region auto fields resolved.

    This keeps old instances safe while letting new instances use a region as a
    convenient source of timezone/language defaults.
    """
    resolved = deepcopy(identity or {})
    region_key = normalize_region_profile_key(resolved.get("region_profile"))
    resolved["region_profile"] = region_key
    resolved["launch_mode"] = normalize_launch_mode(
        resolved.get("launch_mode"),
        default=default_launch_mode,
    )

    profile = get_region_profile(region_key)
    if not profile:
        return resolved

    if bool(resolved.get("region_timezone_auto")) or not resolved.get("timezone"):
        resolved["timezone"] = profile["timezone"]

    if bool(resolved.get("region_language_auto")) or not resolved.get("language"):
        resolved["language"] = profile["language"]

    return resolved


def new_identity_defaults() -> Dict:
    """Defaults used by the Instance Manager for newly created instances."""
    return {
        "region_profile": "",
        "launch_mode": DEFAULT_NEW_LAUNCH_MODE,
        "region_timezone_auto": True,
        "region_language_auto": True,
    }


# Compatibility helpers used by the current GUI code.
def get_region_choices() -> list[tuple[str, str]]:
    choices = [("", "No Region Profile")]
    choices.extend((profile["key"], profile["label"]) for profile in REGION_PROFILES)
    return choices


def get_launch_mode_choices() -> list[tuple[str, str, str]]:
    return [(mode["key"], mode["label"], mode["description"]) for mode in LAUNCH_MODES]


def region_defaults_for_key(value: object) -> Dict[str, str]:
    profile = get_region_profile(value)
    if not profile:
        return {"timezone": "", "language": "", "locale": ""}
    return {
        "timezone": str(profile.get("timezone", "")),
        "language": str(profile.get("language", "")),
        "locale": str(profile.get("locale", "")),
    }


def resolve_identity_settings(identity: Optional[Dict], *, default_launch_mode: str = DEFAULT_LEGACY_LAUNCH_MODE) -> Dict:
    return resolved_identity_settings(identity, default_launch_mode=default_launch_mode)


def get_region_label(value: object) -> str:
    return region_profile_label(value)


def get_launch_mode_label(value: object) -> str:
    return launch_mode_label(value)

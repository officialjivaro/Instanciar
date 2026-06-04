# appdata/logic/browser_profile_health.py
"""Plain-English browser profile health checks for Instanciar."""

from typing import Dict, List

from appdata.logic.region_profile_logic import (
    get_region_profile,
    language_to_code,
    launch_mode_label,
    region_profile_label,
    resolved_identity_settings,
)


def _proxy_is_configured(instance: Dict) -> bool:
    proxy = instance.get("proxy") or {}
    return bool(str(proxy.get("ip") or "").strip() and str(proxy.get("port") or "").strip())


def _warning_list_text(warnings: List[str], limit: int = 3) -> str:
    if not warnings:
        return "None"
    shown = warnings[:limit]
    suffix = f" (+{len(warnings) - limit} more)" if len(warnings) > limit else ""
    return " • ".join(shown) + suffix


def build_browser_profile_health(instance: Dict) -> Dict:
    """
    Return display-ready setup health for a browser instance.

    These checks are informational. They help the user avoid contradictory
    settings, but they do not block saving or launching.
    """
    identity = resolved_identity_settings(instance.get("identity") or {})
    region_key = identity.get("region_profile", "")
    region = get_region_profile(region_key)
    proxy_configured = _proxy_is_configured(instance)

    warnings: List[str] = []
    notes: List[str] = []

    if proxy_configured and not region:
        warnings.append("Proxy is enabled, but no region profile is selected.")

    if region and not proxy_configured:
        notes.append("Region profile changes browser settings, but it does not change your public IP without a proxy.")

    if region:
        timezone = str(identity.get("timezone") or "").strip()
        language_code = language_to_code(identity.get("language"))
        expected_language = str(region.get("locale") or "").strip()

        if timezone and timezone != region.get("timezone"):
            warnings.append(
                f"Timezone is {timezone}, but {region['label']} normally uses {region['timezone']} in this profile."
            )

        if language_code and expected_language and language_code.casefold() != expected_language.casefold():
            warnings.append(
                f"Language is {language_code}, but {region['label']} profile recommends {expected_language}."
            )

    if proxy_configured and not bool(identity.get("webrtc_disabled")):
        warnings.append("WebRTC is enabled while proxy is enabled; this may reveal non-proxy network information.")

    if bool(identity.get("geolocation_enabled")) and not region:
        warnings.append("Geolocation is enabled, but no region profile is selected.")

    status = "warning" if warnings else "ok"
    summary = "Review recommended" if warnings else "Looks consistent"

    return {
        "status": status,
        "summary": summary,
        "warnings": warnings,
        "notes": notes,
        "warning_text": _warning_list_text(warnings),
        "region_label": region_profile_label(region_key),
        "launch_mode_label": launch_mode_label(identity.get("launch_mode")),
        "identity": identity,
    }


def format_health_warnings(warnings: List[str], limit: int = 3) -> str:
    return _warning_list_text(warnings, limit=limit)

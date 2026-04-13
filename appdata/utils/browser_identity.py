# appdata/utils/browser_identity.py
import json
import os
import platform as py_platform
import random
import re
import time
import urllib.request
from typing import Dict, List, Optional

from appdata.config.constants import DEFAULT_UA, LEGACY_COMMON_USER_AGENTS

_CACHE_TTL = 12 * 3600
_CHANNELS_ENDPOINT = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
_MILESTONES_ENDPOINT = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json"

_PLATFORM_PROFILES = {
    "win": {
        "label": "Windows",
        "os_token": "Windows NT 10.0; Win64; x64",
        "navigator_platform": "Win32",
        "platform": "Windows",
        "platform_version": "10.0.0",
        "architecture": "x86",
        "bitness": "64",
        "mobile": False,
        "wow64": False,
        "model": "",
    },
    "mac": {
        "label": "macOS",
        "os_token": "Macintosh; Intel Mac OS X 10_15_7",
        "navigator_platform": "MacIntel",
        "platform": "macOS",
        "platform_version": "10.15.7",
        "architecture": "x86",
        "bitness": "64",
        "mobile": False,
        "wow64": False,
        "model": "",
    },
    "linux": {
        "label": "Linux",
        "os_token": "X11; Linux x86_64",
        "navigator_platform": "Linux x86_64",
        "platform": "Linux",
        "platform_version": "0.0.0",
        "architecture": "x86",
        "bitness": "64",
        "mobile": False,
        "wow64": False,
        "model": "",
    },
    "android": {
        "label": "Android",
        "os_token": "Linux; Android 13",
        "navigator_platform": "Linux armv8l",
        "platform": "Android",
        "platform_version": "13",
        "architecture": "arm",
        "bitness": "64",
        "mobile": True,
        "wow64": False,
        "model": "",
    },
    "ios": {
        "label": "iPhone",
        "os_token": "iPhone; CPU iPhone OS 16_4 like Mac OS X",
        "navigator_platform": "iPhone",
        "platform": "iOS",
        "platform_version": "16.4.0",
        "architecture": "arm",
        "bitness": "64",
        "mobile": True,
        "wow64": False,
        "model": "iPhone",
    },
}
_DESKTOP_PLATFORMS = ("win", "mac", "linux")


def _config_dir() -> str:
    path = os.path.join(os.path.expanduser("~"), "Jivaro", "Instanciar", "config")
    os.makedirs(path, exist_ok=True)
    return path


def _cache_path() -> str:
    return os.path.join(_config_dir(), "browser_identity_cache.json")


def _read_cache() -> Optional[Dict]:
    try:
        with open(_cache_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _write_cache(payload: Dict) -> None:
    try:
        with open(_cache_path(), "w", encoding="utf-8") as fh:
            json.dump({"timestamp": time.time(), "payload": payload}, fh)
    except Exception:
        pass


def _fetch_json(url: str) -> Dict:
    with urllib.request.urlopen(url, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_feed_payload() -> Dict:
    cache = _read_cache()
    if cache and (time.time() - cache.get("timestamp", 0) < _CACHE_TTL):
        payload = cache.get("payload")
        if isinstance(payload, dict):
            return payload

    try:
        payload = {
            "channels": _fetch_json(_CHANNELS_ENDPOINT),
            "milestones": _fetch_json(_MILESTONES_ENDPOINT),
        }
        _write_cache(payload)
        return payload
    except Exception:
        if cache and isinstance(cache.get("payload"), dict):
            return cache["payload"]
        return {"channels": {}, "milestones": {}}


def detect_host_platform() -> str:
    sys_name = py_platform.system().lower()
    if "windows" in sys_name:
        return "win"
    if "darwin" in sys_name or "mac" in sys_name:
        return "mac"
    return "linux"


def _major(version: str) -> str:
    return (version or "126.0.6478.57").split(".")[0]


def _full_version_list(version: str) -> List[Dict[str, str]]:
    major = _major(version)
    return [
        {"brand": "Chromium", "version": version},
        {"brand": "Google Chrome", "version": version},
        {"brand": "Not.A/Brand", "version": "99.0.0.0"},
    ], [
        {"brand": "Chromium", "version": major},
        {"brand": "Google Chrome", "version": major},
        {"brand": "Not.A/Brand", "version": "99"},
    ]


def _build_desktop_user_agent(version: str, platform_key: str) -> str:
    profile = _PLATFORM_PROFILES.get(platform_key, _PLATFORM_PROFILES["win"])
    return (
        f"Mozilla/5.0 ({profile['os_token']}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{version} Safari/537.36"
    )


def _build_identity_bundle(
    *,
    platform_key: str,
    version: str,
    user_agent: Optional[str] = None,
    label: Optional[str] = None,
    preset_key: Optional[str] = None,
    source: str = "resolved",
) -> Dict:
    profile = _PLATFORM_PROFILES.get(platform_key, _PLATFORM_PROFILES["win"])
    ua = user_agent or _build_desktop_user_agent(version, platform_key)
    full_list, brands = _full_version_list(version)
    bundle = {
        "label": label or f"{profile['label']} • Chrome {_major(version)}",
        "preset_key": preset_key or f"{platform_key}:{version}",
        "platform_key": platform_key,
        "platform_label": profile["label"],
        "navigator_platform": profile["navigator_platform"],
        "platform": profile["platform"],
        "platform_version": profile["platform_version"],
        "architecture": profile["architecture"],
        "bitness": profile["bitness"],
        "mobile": profile["mobile"],
        "wow64": profile["wow64"],
        "model": profile["model"],
        "version": version,
        "major_version": _major(version),
        "user_agent": ua,
        "source": source,
    }
    bundle["ua_metadata"] = {
        "brands": brands,
        "fullVersionList": full_list,
        "fullVersion": version,
        "platform": bundle["platform"],
        "platformVersion": bundle["platform_version"],
        "architecture": bundle["architecture"],
        "model": bundle["model"],
        "mobile": bundle["mobile"],
        "bitness": bundle["bitness"],
        "wow64": bundle["wow64"],
    }
    return bundle


def _stable_version() -> str:
    payload = _load_feed_payload().get("channels", {})
    try:
        return payload["channels"]["Stable"]["version"]
    except Exception:
        return _parse_user_agent(DEFAULT_UA)["version"]


def _milestones_map() -> Dict[str, Dict]:
    payload = _load_feed_payload().get("milestones", {})
    milestones = payload.get("milestones")
    return milestones if isinstance(milestones, dict) else {}


def _recent_versions(limit_versions: int = 2) -> List[str]:
    stable = _stable_version()
    versions = [stable]
    milestones = _milestones_map()
    try:
        stable_major = int(_major(stable))
    except Exception:
        stable_major = 126
    milestone = stable_major - 1
    while len(versions) < limit_versions and milestone > 0:
        entry = milestones.get(str(milestone))
        version = entry.get("version") if isinstance(entry, dict) else None
        if version and version not in versions:
            versions.append(version)
        milestone -= 1
    if not versions:
        versions = [_parse_user_agent(DEFAULT_UA)["version"]]
    return versions


def list_recent_real_identities(limit: int = 6) -> List[Dict]:
    identities: List[Dict] = []
    versions = _recent_versions(limit_versions=2)
    stable = _stable_version()
    for version in versions:
        for platform_key in _DESKTOP_PLATFORMS:
            stable_suffix = " (stable)" if version == stable else ""
            label = f"{_PLATFORM_PROFILES[platform_key]['label']} • Chrome {_major(version)}{stable_suffix}"
            identities.append(
                _build_identity_bundle(
                    platform_key=platform_key,
                    version=version,
                    label=label,
                    preset_key=f"{platform_key}:{version}",
                    source="recent",
                )
            )
    return identities[:limit]


def get_latest_stable_identity(platform_key: Optional[str] = None) -> Dict:
    key = platform_key or detect_host_platform()
    version = _stable_version()
    return _build_identity_bundle(
        platform_key=key,
        version=version,
        label=f"{_PLATFORM_PROFILES[key]['label']} • Chrome {_major(version)} (stable)",
        preset_key=f"{key}:{version}",
        source="latest_stable",
    )


def get_recent_identity_by_key(preset_key: str) -> Optional[Dict]:
    if not preset_key or ":" not in preset_key:
        return None
    platform_key, version = preset_key.split(":", 1)
    if platform_key not in _PLATFORM_PROFILES:
        return None
    stable = _stable_version()
    label = f"{_PLATFORM_PROFILES[platform_key]['label']} • Chrome {_major(version)}"
    if version == stable:
        label += " (stable)"
    return _build_identity_bundle(
        platform_key=platform_key,
        version=version,
        label=label,
        preset_key=preset_key,
        source="preset",
    )


def get_random_real_identity(platform_key: Optional[str] = None) -> Dict:
    key = platform_key or detect_host_platform()
    candidates = [ident for ident in list_recent_real_identities(limit=12) if ident["platform_key"] == key]
    if not candidates:
        candidates = [get_latest_stable_identity(key)]
    return random.choice(candidates)


def _parse_user_agent(user_agent: str) -> Dict[str, object]:
    ua = user_agent or DEFAULT_UA
    version_match = re.search(r"(?:Chrome|CriOS)/([0-9]+(?:\.[0-9]+){1,3})", ua)
    version = version_match.group(1) if version_match else "126.0.6478.57"

    if "Android" in ua:
        platform_key = "android"
    elif "iPhone" in ua or "iPad" in ua:
        platform_key = "ios"
    elif "Mac OS X" in ua and "iPhone" not in ua:
        platform_key = "mac"
    elif "Windows NT" in ua:
        platform_key = "win"
    elif "Linux" in ua:
        platform_key = "linux"
    else:
        platform_key = detect_host_platform()

    return {
        "user_agent": ua,
        "version": version,
        "platform_key": platform_key,
        "mobile": "Mobile" in ua or platform_key in {"android", "ios"},
    }


def identity_from_user_agent(user_agent: str, label: Optional[str] = None, preset_key: Optional[str] = None) -> Dict:
    parsed = _parse_user_agent(user_agent)
    platform_key = str(parsed["platform_key"])
    version = str(parsed["version"])
    return _build_identity_bundle(
        platform_key=platform_key,
        version=version,
        user_agent=user_agent,
        label=label or f"Custom • {_PLATFORM_PROFILES[platform_key]['label']} • Chrome {_major(version)}",
        preset_key=preset_key or f"custom:{platform_key}:{version}",
        source="custom",
    )


def normalize_identity_selection(identity: Optional[Dict]) -> Dict[str, str]:
    identity = identity or {}
    mode = (identity.get("browser_identity_mode") or "").strip()
    preset = (identity.get("browser_identity_preset") or "").strip()
    custom_ua = identity.get("custom_user_agent")

    if mode in {"random_real", "latest_stable_real", "preset_real", "custom"}:
        return {
            "mode": mode,
            "preset_key": preset,
            "custom_user_agent": custom_ua or "",
        }

    if custom_ua == "":
        return {"mode": "random_real", "preset_key": "", "custom_user_agent": ""}

    if custom_ua:
        parsed = _parse_user_agent(custom_ua)
        if custom_ua in LEGACY_COMMON_USER_AGENTS and not parsed["mobile"]:
            return {
                "mode": "preset_real",
                "preset_key": f"{parsed['platform_key']}:{parsed['version']}",
                "custom_user_agent": custom_ua,
            }
        return {"mode": "custom", "preset_key": "", "custom_user_agent": custom_ua}

    return {"mode": "custom", "preset_key": "", "custom_user_agent": DEFAULT_UA}


def resolve_browser_identity(identity: Optional[Dict]) -> Dict:
    normalized = normalize_identity_selection(identity)
    mode = normalized["mode"]
    preset_key = normalized["preset_key"]
    custom_ua = normalized["custom_user_agent"]

    if mode == "random_real":
        return get_random_real_identity(detect_host_platform())

    if mode == "latest_stable_real":
        return get_latest_stable_identity(detect_host_platform())

    if mode == "preset_real":
        preset_identity = get_recent_identity_by_key(preset_key)
        if preset_identity is not None:
            return preset_identity
        if custom_ua:
            return identity_from_user_agent(custom_ua, label="Legacy preset")
        return get_latest_stable_identity(detect_host_platform())

    if custom_ua:
        return identity_from_user_agent(custom_ua, label="Custom user agent")

    return identity_from_user_agent(DEFAULT_UA, label="Default browser identity")
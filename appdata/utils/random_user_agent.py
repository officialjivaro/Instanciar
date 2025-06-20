# appdata/utils/random_user_agent.py
import os, json, time, random, urllib.request

_CACHE      = os.path.join(os.path.dirname(__file__), "chrome_versions_cache.json")
_CACHE_TTL  = 7 * 24 * 3600
_ENDPOINT   = "https://omahaproxy.appspot.com/all.json"

_OS_CHOICES = [
    ("Windows NT 10.0; Win64; x64",             False, "win"),
    ("Macintosh; Intel Mac OS X 10_15_7",       False, "mac"),
    ("X11; Linux x86_64",                       False, "linux"),
    ("Linux; Android 13",                       True,  "android"),
    ("iPhone; CPU iPhone OS 16_4 like Mac OS X",True,  "ios"),
]

def _load_versions():
    try:
        if time.time() - os.path.getmtime(_CACHE) < _CACHE_TTL:
            with open(_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    try:
        data = json.loads(urllib.request.urlopen(_ENDPOINT, timeout=5).read().decode())
        out = {}
        for entry in data:
            os_key = entry["os"]
            if os_key not in ("win", "mac", "linux", "android", "ios"):
                continue
            stable = next((c for c in entry["versions"] if c["channel"] == "stable"), None)
            if stable:
                out.setdefault(os_key, []).append(stable["current_version"])
        for k, v in out.items():
            v.sort(key=lambda s: [int(x) for x in s.split(".")], reverse=True)
            out[k] = v[:10]
        with open(_CACHE, "w", encoding="utf-8") as f:
            json.dump(out, f)
        return out
    except Exception:
        return {}

_VERSIONS = _load_versions()

def _pick_version(platform):
    pool = _VERSIONS.get(platform) or ["126.0.6478.57"]
    weights = list(reversed(range(1, len(pool) + 1)))
    return random.choices(pool, weights=weights, k=1)[0]

def generate_random_user_agent():
    os_token, is_mobile, platform = random.choice(_OS_CHOICES)
    chrome_version = _pick_version(platform)
    mobile_tag = "Mobile " if is_mobile else ""
    return (
        f"Mozilla/5.0 ({os_token}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"{mobile_tag}Chrome/{chrome_version} Safari/537.36"
    )

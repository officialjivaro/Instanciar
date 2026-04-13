# appdata/utils/chrome_builder.py
from typing import Dict, Optional

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType

from appdata.config.constants import LANG_CODE_MAP
from appdata.utils.browser_identity import resolve_browser_identity
from appdata.utils.resource_helpers import build_auth_extension


def _proxy_server_arg(proxy: Dict) -> str:
    """Build Chrome's --proxy-server value in a format Chrome expects."""
    address = str(proxy.get("ip", "")).strip()
    port = str(proxy.get("port", "")).strip()
    proto = str(proxy.get("protocol", "HTTP")).strip().lower()

    if proto not in {"http", "https", "socks4", "socks5"}:
        proto = "http"

    return f"{proto}://{address}:{port}"


def _apply_proxy(opt: ChromeOptions, proxy: Dict) -> bool:
    """
    Apply proxy settings to Chrome options.

    Returns True when an auth extension was added, so the caller can avoid
    disabling all extensions for that launch.
    """
    address = str(proxy.get("ip", "")).strip()
    port = str(proxy.get("port", "")).strip()
    proto = str(proxy.get("protocol", "HTTP")).strip().lower()
    auth = bool(proxy.get("auth"))
    user = str(proxy.get("user", "")).strip()
    pwd = str(proxy.get("password", "")).strip()

    if proto not in {"http", "https", "socks4", "socks5"}:
        proto = "http"

    # Add Chrome's own proxy-server argument so proxy routing is set from startup.
    opt.add_argument(f"--proxy-server={_proxy_server_arg(proxy)}")

    px = Proxy()
    px.proxy_type = ProxyType.MANUAL
    px.autodetect = False

    uses_auth_extension = False

    if proto in ("http", "https"):
        px.http_proxy = f"{address}:{port}"
        px.ssl_proxy = f"{address}:{port}"

        # For HTTP/HTTPS proxy auth, keep the existing extension-based approach.
        if auth and user and pwd:
            opt.add_extension(build_auth_extension(proto, address, port, user, pwd))
            uses_auth_extension = True
    else:
        px.socks_proxy = f"{address}:{port}"
        px.socks_version = 4 if proto == "socks4" else 5

        # Preserve the current SOCKS auth capability path.
        if auth and user and pwd:
            px.socks_username = user
            px.socks_password = pwd

    opt.set_capability("proxy", px.to_capabilities())
    return uses_auth_extension


def build_chrome_options(
    identity: Optional[Dict],
    hwid: Optional[str],
    proxy: Optional[Dict],
    identity_bundle: Optional[Dict] = None,
) -> ChromeOptions:
    """Build Chrome options using one resolved browser identity bundle."""
    opt = ChromeOptions()

    # Keep launch-time privacy and startup noise reductions conservative.
    opt.add_argument("--ignore-certificate-errors")
    opt.add_argument("--allow-insecure-localhost")
    opt.add_argument("--disable-background-networking")
    opt.add_argument("--disable-component-update")
    opt.add_argument("--disable-default-apps")
    opt.add_argument("--disable-domain-reliability")
    opt.add_argument("--disable-sync")
    opt.add_argument("--no-first-run")
    opt.add_argument("--no-default-browser-check")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_argument("--disable-features=Translate,MediaRouter,OptimizationHints")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--disable-software-rasterizer")
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])
    opt.add_experimental_option("useAutomationExtension", False)
    opt.set_capability("acceptInsecureCerts", True)

    identity_bundle = identity_bundle or resolve_browser_identity(identity)

    prefs = {
        # Keep browser prompts and background profile services quieter.
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "autofill.profile_enabled": False,
        "autofill.credit_card_enabled": False,
        "dns_prefetching_enabled": False,
        "translate.enabled": False,
    }

    language = LANG_CODE_MAP.get((identity or {}).get("language"), (identity or {}).get("language"))
    if language:
        opt.add_argument(f"--lang={language}")
        prefs["intl.accept_languages"] = language

    geolocation_enabled = (identity or {}).get("geolocation_enabled")
    if geolocation_enabled is True:
        prefs["profile.default_content_setting_values.geolocation"] = 1
    elif geolocation_enabled is False:
        prefs["profile.default_content_setting_values.geolocation"] = 2

    if (identity or {}).get("webrtc_disabled"):
        # These give the WebRTC toggle a browser-level effect before page scripts run.
        prefs["webrtc.ip_handling_policy"] = "disable_non_proxied_udp"
        prefs["webrtc.multiple_routes_enabled"] = False
        prefs["webrtc.nonproxied_udp_enabled"] = False
        opt.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")

    if prefs:
        opt.add_experimental_option("prefs", prefs)

    # Apply UA from startup, then CDP can reinforce it later with matching metadata.
    opt.add_argument(f'--user-agent={identity_bundle["user_agent"]}')

    proxy_uses_extension = False
    if proxy:
        proxy_uses_extension = _apply_proxy(opt, proxy)

    # Do not disable all extensions when a proxy auth extension is needed.
    if not proxy_uses_extension:
        opt.add_argument("--disable-extensions")

    return opt
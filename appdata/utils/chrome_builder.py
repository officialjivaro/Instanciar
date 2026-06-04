# appdata/utils/chrome_builder.py
from typing import Dict, Optional

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType

from appdata.config.constants import LANG_CODE_MAP
from appdata.logic.region_profile_logic import normalize_launch_mode
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

    opt.add_argument(f"--proxy-server={_proxy_server_arg(proxy)}")

    px = Proxy()
    px.proxy_type = ProxyType.MANUAL
    px.autodetect = False

    uses_auth_extension = False

    if proto in ("http", "https"):
        px.http_proxy = f"{address}:{port}"
        px.ssl_proxy = f"{address}:{port}"

        if auth and user and pwd:
            opt.add_extension(build_auth_extension(proto, address, port, user, pwd))
            uses_auth_extension = True
    else:
        px.socks_proxy = f"{address}:{port}"
        px.socks_version = 4 if proto == "socks4" else 5

        if auth and user and pwd:
            px.socks_username = user
            px.socks_password = pwd

    opt.set_capability("proxy", px.to_capabilities())
    return uses_auth_extension


def _apply_launch_mode_options(opt: ChromeOptions, launch_mode: str) -> None:
    """
    Apply launch-mode-specific Chrome options.

    Normal mode intentionally uses fewer startup restrictions so Chrome behaves
    closer to a regular user profile. Privacy mode preserves the previous quiet,
    stricter behavior for users who prefer it.
    """
    opt.add_argument("--no-first-run")
    opt.add_argument("--no-default-browser-check")
    opt.set_capability("acceptInsecureCerts", True)

    if launch_mode != "privacy":
        return

    opt.add_argument("--ignore-certificate-errors")
    opt.add_argument("--allow-insecure-localhost")
    opt.add_argument("--disable-background-networking")
    opt.add_argument("--disable-component-update")
    opt.add_argument("--disable-default-apps")
    opt.add_argument("--disable-domain-reliability")
    opt.add_argument("--disable-sync")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_argument("--disable-features=Translate,MediaRouter,OptimizationHints")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--disable-software-rasterizer")
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])
    opt.add_experimental_option("useAutomationExtension", False)


def _base_prefs(launch_mode: str) -> Dict:
    prefs: Dict = {}

    if launch_mode == "privacy":
        prefs.update(
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "autofill.profile_enabled": False,
                "autofill.credit_card_enabled": False,
                "dns_prefetching_enabled": False,
                "translate.enabled": False,
            }
        )

    return prefs


def build_chrome_options(
    identity: Optional[Dict],
    hwid: Optional[str],
    proxy: Optional[Dict],
    identity_bundle: Optional[Dict] = None,
    launch_mode: Optional[str] = None,
) -> ChromeOptions:
    """Build Chrome options using one resolved browser identity bundle."""
    opt = ChromeOptions()
    identity = identity or {}
    launch_mode = normalize_launch_mode(launch_mode or identity.get("launch_mode"))

    _apply_launch_mode_options(opt, launch_mode)
    identity_bundle = identity_bundle or resolve_browser_identity(identity)

    prefs = _base_prefs(launch_mode)

    language = LANG_CODE_MAP.get(identity.get("language"), identity.get("language"))
    if language:
        opt.add_argument(f"--lang={language}")
        prefs["intl.accept_languages"] = language

    geolocation_enabled = identity.get("geolocation_enabled")
    if geolocation_enabled is True:
        prefs["profile.default_content_setting_values.geolocation"] = 1
    elif geolocation_enabled is False:
        prefs["profile.default_content_setting_values.geolocation"] = 2

    if identity.get("webrtc_disabled"):
        prefs["webrtc.ip_handling_policy"] = "disable_non_proxied_udp"
        prefs["webrtc.multiple_routes_enabled"] = False
        prefs["webrtc.nonproxied_udp_enabled"] = False
        opt.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")

    if prefs:
        opt.add_experimental_option("prefs", prefs)

    opt.add_argument(f'--user-agent={identity_bundle["user_agent"]}')

    proxy_uses_extension = False
    if proxy:
        proxy_uses_extension = _apply_proxy(opt, proxy)

    # Privacy mode keeps the old quiet extension behavior. Normal mode does not
    # disable extensions because a regular profile should behave closer to Chrome.
    if launch_mode == "privacy" and not proxy_uses_extension:
        opt.add_argument("--disable-extensions")

    return opt

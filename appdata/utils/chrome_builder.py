# appdata/utils/chrome_builder.py
import os
from typing import Dict, Optional
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType
from appdata.config.constants import DEFAULT_UA
from appdata.utils.resource_helpers import build_auth_extension
from appdata.utils.random_user_agent import generate_random_user_agent

def _apply_proxy(opt: ChromeOptions, proxy: Dict) -> None:
    address, port = proxy["ip"], proxy["port"]
    proto = proxy["protocol"].lower()
    auth, user, pwd = proxy.get("auth"), proxy.get("user"), proxy.get("password")
    px = Proxy()
    px.proxy_type = ProxyType.MANUAL
    px.autodetect = False
    if proto in ("http", "https"):
        px.http_proxy = f"{address}:{port}"
        px.ssl_proxy = f"{address}:{port}"
        if auth and user and pwd:
            opt.add_extension(build_auth_extension(proto, address, port, user, pwd))
    else:
        px.socks_proxy = f"{address}:{port}"
        px.socks_version = 4 if proto == "socks4" else 5
        if auth and user and pwd:
            px.socks_username, px.socks_password = user, pwd
    opt.set_capability("proxy", px.to_capabilities())

def build_chrome_options(identity: Optional[Dict], hwid: Optional[str], proxy: Optional[Dict]) -> ChromeOptions:
    opt = ChromeOptions()
    opt.add_argument("--disable-extensions")
    opt.add_argument("--ignore-certificate-errors")
    opt.add_argument("--allow-insecure-localhost")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--disable-software-rasterizer")
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])
    opt.add_experimental_option("useAutomationExtension", False)
    if identity and (lang := identity.get("language")):
        opt.add_argument(f"--lang={lang}")
    if identity is not None:
        cu = identity.get("custom_user_agent", None)
        if cu == "":
            ua = generate_random_user_agent()
        elif cu:
            ua = cu
        else:
            ua = DEFAULT_UA
    else:
        ua = DEFAULT_UA
    opt.add_argument(f"user-agent={ua}")
    opt.set_capability("acceptInsecureCerts", True)
    if proxy:
        _apply_proxy(opt, proxy)
    return opt

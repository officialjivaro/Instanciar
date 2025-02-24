# logic/browser_manager.py
import os
import sys
import platform
import tempfile
import zipfile
import base64
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType

try:
    from selenium.webdriver.safari.webdriver import WebDriver as SafariDriver
    SAFARI_AVAILABLE = True
except ImportError:
    SAFARI_AVAILABLE = False

class BrowserManager:
    def launch(self, instance, browser, block_scripts):
        fid = instance["folder_id"]
        user_folder = os.path.expanduser("~")
        base_path = os.path.join(user_folder, "Jivaro", "Instanciar", "instances")
        instance_path = os.path.join(base_path, fid)
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        hwid_info = None
        if "hwid" in instance and instance["hwid"].get("enabled"):
            hwid_file = os.path.join(instance_path, "hwid.txt")
            if not os.path.exists(hwid_file):
                hwid_txt = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                with open(hwid_file, "w", encoding="utf-8") as f:
                    f.write(hwid_txt)
            with open(hwid_file, "r", encoding="utf-8") as f:
                hwid_info = f.read().strip()
        b = browser.lower()
        if b == "safari":
            if SAFARI_AVAILABLE and platform.system().lower() == "darwin":
                self.launch_safari(instance, instance_path, block_scripts, hwid_info)
            else:
                self.launch_chrome(instance, instance_path, block_scripts, hwid_info)
        elif b == "firefox":
            self.launch_firefox(instance, instance_path, block_scripts, hwid_info)
        else:
            self.launch_chrome(instance, instance_path, block_scripts, hwid_info)

    def launch_chrome(self, instance, path, block_scripts, hwid_info):
        opt = ChromeOptions()
        opt.add_argument("--user-data-dir=" + path)
        opt.add_argument("--disable-extensions")
        opt.add_argument("--ignore-certificate-errors")
        opt.add_argument("--allow-insecure-localhost")
        opt.add_argument("--disable-blink-features=AutomationControlled")
        opt.add_experimental_option("excludeSwitches", ["enable-automation"])
        opt.add_experimental_option("useAutomationExtension", False)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.205 Safari/537.36"
        if hwid_info:
            ua += " HWID/" + hwid_info
        opt.add_argument("user-agent=" + ua)
        opt.set_capability("acceptInsecureCerts", True)
        if instance.get("proxy"):
            self.apply_chrome_proxy(opt, instance["proxy"])
        driver = None
        try:
            driver = webdriver.Chrome(options=opt)
        except Exception as ex:
            if "extension" in str(ex).lower() and "session not created" in str(ex).lower():
                opt.extensions = []
                driver = webdriver.Chrome(options=opt)
            else:
                raise
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        if block_scripts:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": self.get_block_script()
            })
        driver.get("https://www.duckduckgo.com")

    def launch_firefox(self, instance, path, block_scripts, hwid_info):
        opts = FirefoxOptions()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.205 Safari/537.36"
        if hwid_info:
            ua += " HWID/" + hwid_info
        opts.set_preference("general.useragent.override", ua)
        opts.set_capability("acceptInsecureCerts", True)
        opts.set_preference("security.insecure_field_warning.contextual.enabled", False)
        opts.set_preference("webdriver_accept_untrusted_certs", True)
        opts.set_preference("webdriver_assume_untrusted_issuer", False)
        if instance.get("proxy"):
            self.apply_firefox_proxy(opts, instance["proxy"])
        driver = webdriver.Firefox(options=opts)
        if block_scripts:
            driver.execute_script(self.get_block_script())
        driver.get("https://www.duckduckgo.com")

    def launch_safari(self, instance, path, block_scripts, hwid_info):
        try:
            if not SAFARI_AVAILABLE or platform.system().lower() != "darwin":
                raise RuntimeError("Safari not available on this platform.")
            drv = SafariDriver()
            if block_scripts:
                try:
                    drv.execute_script(self.get_block_script())
                except:
                    pass
            drv.get("https://www.duckduckgo.com")
        except Exception:
            self.launch_chrome(instance, path, block_scripts, hwid_info)

    def apply_chrome_proxy(self, opt, p):
        address = p["ip"]
        port = p["port"]
        protocol = p["protocol"].lower()
        auth_enabled = p["auth"]
        user = p["user"] if auth_enabled else None
        password = p["password"] if auth_enabled else None
        px = Proxy()
        px.proxy_type = ProxyType.MANUAL
        px.autodetect = False
        if protocol == "http":
            px.http_proxy = address + ":" + port
            px.ssl_proxy = address + ":" + port
            if auth_enabled and user and password:
                ext = self.build_auth_extension("http", address, port, user, password)
                opt.add_extension(ext)
        elif protocol == "https":
            px.http_proxy = address + ":" + port
            px.ssl_proxy = address + ":" + port
            if auth_enabled and user and password:
                ext = self.build_auth_extension("https", address, port, user, password)
                opt.add_extension(ext)
        elif protocol == "socks4":
            px.socks_proxy = address + ":" + port
            px.socks_version = 4
            if auth_enabled and user and password:
                px.socks_username = user
                px.socks_password = password
        elif protocol == "socks5":
            px.socks_proxy = address + ":" + port
            px.socks_version = 5
            if auth_enabled and user and password:
                px.socks_username = user
                px.socks_password = password
        caps = px.to_capabilities()
        opt.set_capability("proxy", caps)

    def apply_firefox_proxy(self, opts, p):
        address = p["ip"]
        port = p["port"]
        protocol = p["protocol"].lower()
        auth_enabled = p["auth"]
        user = p["user"] if auth_enabled else None
        password = p["password"] if auth_enabled else None
        opts.set_preference("network.proxy.type", 1)
        if protocol in ["http", "https"]:
            opts.set_preference("network.proxy.http", address)
            opts.set_preference("network.proxy.http_port", int(port))
            opts.set_preference("network.proxy.ssl", address)
            opts.set_preference("network.proxy.ssl_port", int(port))
        elif protocol == "socks4":
            opts.set_preference("network.proxy.socks", address)
            opts.set_preference("network.proxy.socks_port", int(port))
            opts.set_preference("network.proxy.socks_version", 4)
            if auth_enabled and user and password:
                opts.set_preference("network.proxy.socks_username", user)
                opts.set_preference("network.proxy.socks_password", password)
        elif protocol == "socks5":
            opts.set_preference("network.proxy.socks", address)
            opts.set_preference("network.proxy.socks_port", int(port))
            opts.set_preference("network.proxy.socks_version", 5)
            if auth_enabled and user and password:
                opts.set_preference("network.proxy.socks_username", user)
                opts.set_preference("network.proxy.socks_password", password)

    def build_auth_extension(self, protocol, host, port, user, password):
        background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
      singleProxy: {{
        scheme: "{protocol}",
        host: "{host}",
        port: parseInt("{port}")
      }},
      bypassList: []
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{user}",
            password: "{password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
        """
        manifest_json = """
{
  "version": "1.0.0",
  "manifest_version": 2,
  "name": "Chrome Proxy Auth Extension",
  "permissions": [
    "proxy",
    "tabs",
    "unlimitedStorage",
    "storage",
    "<all_urls>",
    "webRequest",
    "webRequestBlocking"
  ],
  "background": {
    "scripts": ["background.js"]
  }
}
        """
        d = tempfile.mkdtemp()
        bg_path = os.path.join(d, "background.js")
        mf_path = os.path.join(d, "manifest.json")
        with open(bg_path, "w", encoding="utf-8") as bg:
            bg.write(background_js)
        with open(mf_path, "w", encoding="utf-8") as mf:
            mf.write(manifest_json)
        zip_path = os.path.join(d, "proxy_auth_extension.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(bg_path, "background.js")
            zf.write(mf_path, "manifest.json")
        return zip_path

    def get_block_script(self):
        return """
document.addEventListener('copy', e => { e.stopImmediatePropagation(); e.preventDefault(); }, true);
document.addEventListener('cut', e => { e.stopImmediatePropagation(); e.preventDefault(); }, true);
document.addEventListener('paste', e => { e.stopImmediatePropagation(); e.preventDefault(); }, true);
document.addEventListener('selectstart', e => { e.stopImmediatePropagation(); }, true);
document.addEventListener('keydown', e => {
    if (e.key === 'PrintScreen') {
        e.stopImmediatePropagation();
        e.preventDefault();
    }
}, true);
"""

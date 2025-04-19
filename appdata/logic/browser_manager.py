# logic/browser_manager.py
import os
import random
import string
import tempfile
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType

class BrowserManager:
    def launch(self, instance, _, __):
        folder_id = instance["folder_id"]
        user_folder = os.path.expanduser("~")
        base_path = os.path.join(user_folder, "Jivaro", "Instanciar", "instances")
        instance_path = os.path.join(base_path, folder_id)
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

        block_scripts = False
        identity_data = None

        if "antidetect" in instance and instance["antidetect"].get("enabled"):
            block_scripts = True
            if "identity" in instance:
                identity_data = instance["identity"]

        self.launch_chrome(instance, instance_path, block_scripts, hwid_info, identity_data)

    def launch_chrome(self, instance, path, block_scripts, hwid_info, identity):
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

        if identity and "custom_user_agent" in identity and identity["custom_user_agent"]:
            ua = identity["custom_user_agent"]
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

        # Remove navigator.webdriver for stealth
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        if identity and "timezone" in identity and identity["timezone"]:
            tz_code = identity["timezone"]
            tz_script = f'''
            Intl.DateTimeFormat = class extends Intl.DateTimeFormat {{
                resolvedOptions() {{
                    return {{
                        timeZone: "{tz_code}"
                    }}
                }}
            }};
            '''
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": tz_script})

        if identity and "language" in identity and identity["language"]:
            lang = identity["language"]
            opt.add_argument(f"--lang={lang}")

        if identity and "webrtc_disabled" in identity and identity["webrtc_disabled"]:
            opt.add_argument("--disable-webrtc")

        if identity and "geolocation_enabled" in identity:
            if not identity["geolocation_enabled"]:
                geo_script = "navigator.geolocation = undefined;"
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": geo_script})

        if block_scripts:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": self.get_block_script()
            })

        driver.get("https://www.duckduckgo.com")

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

        if protocol == "http" or protocol == "https":
            px.http_proxy = address + ":" + port
            px.ssl_proxy = address + ":" + port
            if auth_enabled and user and password:
                ext = self.build_auth_extension(protocol, address, port, user, password)
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
        """
        Let copy/paste/PrintScreen work locally, but hide them from the webpage.
        We do this by simply stopping the event's propagation or spoofing its key,
        so the site doesn't detect it as 'PrintScreen' or 'copy' etc.
        """
        return r"""
(function() {
  // Sites won't see the real 'PrintScreen'. We'll rename it so they can't detect the key.
  document.addEventListener('keydown', function(e) {
    if (e.key === 'PrintScreen') {
      Object.defineProperty(e, 'key', {
        value: 'Unidentified',
        configurable: true
      });
      e.stopPropagation();
    }
  }, true);

  // For copy, cut, paste, we let the browser do them locally, 
  // but we block the event from reaching the page's JS listeners.
  ['copy','cut','paste'].forEach(function(evtType) {
    document.addEventListener(evtType, function(e) {
      e.stopPropagation();
      // No preventDefault here, so your local copy/paste/cut still happens.
    }, true);
  });

  // For 'selectstart', same approach
  document.addEventListener('selectstart', function(e) {
    e.stopPropagation();
  }, true);
})();
        """

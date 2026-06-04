# appdata/utils/resource_helpers.py
import os, tempfile, zipfile, textwrap

def rp(rel_path: str) -> str:
    """Resolve project-relative resources in source and PyInstaller builds."""
    import sys

    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # appdata/utils -> project root
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base, rel_path)

def build_auth_extension(protocol: str, host: str, port: str, user: str, password: str) -> str:
    bg = textwrap.dedent(f"""
        var config={{mode:"fixed_servers",rules:{{singleProxy:{{scheme:"{protocol}",host:"{host}",port:parseInt("{port}")}},bypassList:[]}}}};
        chrome.proxy.settings.set({{value:config,scope:"regular"}},function(){{}});
        function cb(details){{return{{authCredentials:{{username:"{user}",password:"{password}"}}}};}}
        chrome.webRequest.onAuthRequired.addListener(cb,{{urls:["<all_urls>"]}},['blocking']);
    """)
    mf = textwrap.dedent("""
        {
          "version": "1.0.0",
          "manifest_version": 2,
          "name": "Chrome Proxy Auth Extension",
          "permissions": [
            "proxy","tabs","unlimitedStorage","storage","<all_urls>",
            "webRequest","webRequestBlocking"
          ],
          "background": { "scripts": ["background.js"] }
        }
    """)
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "background.js"), "w", encoding="utf-8") as f: f.write(bg)
    with open(os.path.join(d, "manifest.json"),  "w", encoding="utf-8") as f: f.write(mf)
    zpath = os.path.join(d, "proxy_auth_extension.zip")
    with zipfile.ZipFile(zpath, "w") as z:
        z.write(os.path.join(d, "background.js"), "background.js")
        z.write(os.path.join(d, "manifest.json"), "manifest.json")
    return zpath

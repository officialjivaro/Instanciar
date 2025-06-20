# appdata/utils/__init__.py
import os, sys, tempfile, zipfile, textwrap

def rp(rel_path: str) -> str:
    base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
          "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],
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

def get_block_script() -> str:
    return r"""
(function(){
  document.addEventListener('keydown',e=>{if(e.key==='PrintScreen'){Object.defineProperty(e,'key',{value:'Unidentified',configurable:true});e.stopPropagation();}},true);
  ['copy','cut','paste'].forEach(t=>document.addEventListener(t,e=>e.stopPropagation(),true));
  document.addEventListener('selectstart',e=>e.stopPropagation(),true);
})();
"""

from .io_helpers import safe_json_read, safe_json_write  # re‑export
from .chrome_builder import build_chrome_options        # re‑export

__all__ = [
    "rp",
    "build_auth_extension",
    "get_block_script",
    "safe_json_read",
    "safe_json_write",
    "build_chrome_options",
]

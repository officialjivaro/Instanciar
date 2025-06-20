# appdata/logic/browser_manager.py
import os, json, random, string, time, re
from contextlib import suppress
from typing import Dict, Optional
from selenium import webdriver
from appdata.utils.chrome_builder import build_chrome_options
from appdata.utils.resource_helpers import get_block_script
from appdata.config.constants import TIME_ZONE_MAP, LANG_CODE_MAP


class BrowserManager:
    def launch(self, instance: Dict):
        folder_id = instance["folder_id"]
        root = os.path.join(os.path.expanduser("~"), "Jivaro", "Instanciar", "instances")
        inst_path = os.path.join(root, folder_id)
        os.makedirs(inst_path, exist_ok=True)
        hwid: Optional[str] = None
        if instance.get("hwid", {}).get("enabled"):
            hwid = "".join(random.choices(string.ascii_letters + string.digits, k=32))
            with open(os.path.join(inst_path, "hwid.txt"), "w", encoding="utf-8") as f:
                f.write(hwid)
        identity = instance.get("identity") if instance.get("antidetect", {}).get("enabled") else None
        opt = build_chrome_options(identity, hwid, instance.get("proxy"))
        opt.add_argument(f"--user-data-dir={inst_path}")
        driver = self._create_driver(opt)
        try:
            self._apply_spoof(driver, identity, hwid)
            if instance.get("antidetect", {}).get("enabled"):
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": get_block_script()})
            driver.get(instance.get("landing_page", "https://www.duckduckgo.com"))
            while True:
                try:
                    _ = driver.title
                    time.sleep(1)
                except Exception:
                    break
        finally:
            with suppress(Exception):
                driver.quit()

    def _create_driver(self, opt):
        try:
            return webdriver.Chrome(options=opt)
        except Exception as ex:
            if "session not created" in str(ex).lower() and "extension" in str(ex).lower():
                opt.extensions = []
                return webdriver.Chrome(options=opt)
            raise

    def _ua_metadata(self, ua: str):
        m = re.search(r"Chrome/(\d+)\.(\d+\.\d+\.\d+)", ua) or re.search(r"CriOS/(\d+)\.(\d+\.\d+\.\d+)", ua)
        full = m.group(0).split("/")[1] if m else "126.0.0.0"
        major = full.split(".")[0]
        return {
            "brands": [{"brand": "Chromium", "version": major}, {"brand": "Not;A=Brand", "version": "99"}],
            "fullVersion": full,
            "platform": "",
            "platformVersion": "0.0.0",
            "architecture": "",
            "model": "",
            "mobile": "Mobile" in ua,
            "bitness": "64",
        }

    def _apply_spoof(self, driver, identity, hwid):
        wd_script = "(()=>{try{delete Object.getPrototypeOf(navigator).webdriver}catch(e){}})();"
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": wd_script})
        ua_override = None
        locale_override = None
        tz_override = None
        if identity:
            tz_raw = identity.get("timezone")
            if tz_raw:
                tz_override = TIME_ZONE_MAP.get(tz_raw, tz_raw)
            loc_raw = identity.get("language")
            if loc_raw:
                locale_override = LANG_CODE_MAP.get(loc_raw, loc_raw)
            cu = identity.get("custom_user_agent")
            if cu == "":
                ua_override = driver.execute_cdp_cmd("Browser.getVersion", {})["userAgent"]
            elif cu:
                ua_override = cu
        if not ua_override:
            ua_override = driver.execute_cdp_cmd("Browser.getVersion", {})["userAgent"]
        metadata = self._ua_metadata(ua_override)
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": ua_override, "platform": "", "userAgentMetadata": metadata},
        )
        if tz_override:
            with suppress(Exception):
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": tz_override})
        if locale_override:
            with suppress(Exception):
                driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": locale_override})
        headers = {}
        if hwid:
            headers["X-Instanciar-HWID"] = hwid
        if headers:
            driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
        driver.execute_cdp_cmd("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True})
        self._recurse_existing_targets(driver, ua_override, metadata, tz_override, locale_override, headers, wd_script)

    def _recurse_existing_targets(self, driver, ua, meta, tz, loc, headers, wd_script):
        allowed = {"page", "iframe", "worker", "service_worker", "shared_worker", "sub_frame"}
        skip = ("chrome://", "devtools://", "about:", "edge://")
        for tgt in driver.execute_cdp_cmd("Target.getTargets", {})["targetInfos"]:
            if tgt.get("type") not in allowed or tgt.get("url", "").startswith(skip):
                continue
            tid = tgt["targetId"]
            sid = driver.execute_cdp_cmd("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
            driver.execute_cdp_cmd(
                "Target.sendMessageToTarget",
                {"sessionId": sid, "message": json.dumps({"id": 1, "method": "Page.addScriptToEvaluateOnNewDocument", "params": {"source": wd_script}})},
            )
            driver.execute_cdp_cmd(
                "Target.sendMessageToTarget",
                {"sessionId": sid, "message": json.dumps({"id": 2, "method": "Network.setUserAgentOverride", "params": {"userAgent": ua, "platform": "", "userAgentMetadata": meta}})},
            )
            if tz:
                driver.execute_cdp_cmd(
                    "Target.sendMessageToTarget",
                    {"sessionId": sid, "message": json.dumps({"id": 3, "method": "Emulation.setTimezoneOverride", "params": {"timezoneId": tz}})},
                )
            if loc:
                driver.execute_cdp_cmd(
                    "Target.sendMessageToTarget",
                    {"sessionId": sid, "message": json.dumps({"id": 4, "method": "Emulation.setLocaleOverride", "params": {"locale": loc}})},
                )
            if headers:
                driver.execute_cdp_cmd(
                    "Target.sendMessageToTarget",
                    {"sessionId": sid, "message": json.dumps({"id": 5, "method": "Network.setExtraHTTPHeaders", "params": {"headers": headers}})},
                )
            driver.execute_cdp_cmd("Target.detachFromTarget", {"sessionId": sid})

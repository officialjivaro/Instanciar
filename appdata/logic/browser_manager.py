# appdata/logic/browser_manager.py
import json
import os
import random
import string
import threading
import time
from contextlib import suppress
from typing import Dict, Optional

from selenium import webdriver

from appdata.config.constants import TIME_ZONE_MAP, LANG_CODE_MAP
from appdata.utils.browser_identity import resolve_browser_identity
from appdata.utils.chrome_builder import build_chrome_options
from appdata.utils.resource_helpers import get_block_script


class BrowserManager:
    """Launch and maintain browser sessions using one resolved identity bundle per instance."""

    def __init__(self):
        self._live_sessions = {}
        self._session_lock = threading.Lock()

    def _new_launch_result(self) -> Dict:
        return {
            "started": False,
            "privacy_ok": True,
            "warnings": [],
            "steps": {},
            "step_errors": {},
        }

    def _short_error(self, error) -> str:
        if isinstance(error, BaseException):
            message = str(error).strip() or error.__class__.__name__
        else:
            message = str(error).strip()

        if len(message) > 140:
            return message[:137] + "..."
        return message

    def _set_step_status(self, launch_result: Dict, key: str, status, label: str = "", error=None) -> None:
        launch_result["steps"][key] = status

        if status is False:
            launch_result["privacy_ok"] = False
            label_text = label or key.replace("_", " ")

            if label_text and label_text not in launch_result["warnings"]:
                launch_result["warnings"].append(label_text)

            if error is not None:
                launch_result["step_errors"][key] = self._short_error(error)
            else:
                launch_result["step_errors"].pop(key, None)
        else:
            launch_result["step_errors"].pop(key, None)

    def _finalize_launch_result(self, launch_result: Dict) -> Dict:
        # Remove duplicates while preserving order.
        launch_result["warnings"] = list(dict.fromkeys(launch_result.get("warnings", [])))
        launch_result["privacy_ok"] = not bool(launch_result["warnings"])
        return launch_result

    def launch(self, instance: Dict):
        folder_id = instance["folder_id"]
        root = os.path.join(os.path.expanduser("~"), "Jivaro", "Instanciar", "instances")
        inst_path = os.path.join(root, folder_id)
        os.makedirs(inst_path, exist_ok=True)

        hwid: Optional[str] = None
        if instance.get("hwid", {}).get("enabled"):
            hwid = "".join(random.choices(string.ascii_letters + string.digits, k=32))
            with open(os.path.join(inst_path, "hwid.txt"), "w", encoding="utf-8") as fh:
                fh.write(hwid)

        identity_settings = instance.get("identity") or {}
        identity_bundle = resolve_browser_identity(identity_settings)

        options = build_chrome_options(identity_settings, hwid, instance.get("proxy"), identity_bundle)
        options.add_argument(f"--user-data-dir={inst_path}")

        launch_result = self._new_launch_result()
        driver = self._create_driver(options)
        try:
            self._apply_spoof(driver, identity_settings, identity_bundle, launch_result)

            if instance.get("antidetect", {}).get("enabled"):
                try:
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": get_block_script()})
                except Exception as exc:
                    self._set_step_status(
                        launch_result,
                        "antidetect_script",
                        False,
                        "anti-detect script",
                        exc,
                    )
                else:
                    self._set_step_status(launch_result, "antidetect_script", True)
            else:
                self._set_step_status(launch_result, "antidetect_script", None)

            driver.get(instance.get("landing_page", "https://www.duckduckgo.com"))
            _ = driver.current_url
        except Exception:
            with suppress(Exception):
                driver.quit()
            raise

        with self._session_lock:
            self._live_sessions[folder_id] = driver

        threading.Thread(target=self._monitor_session, args=(folder_id, driver), daemon=True).start()

        launch_result["started"] = True
        return self._finalize_launch_result(launch_result)

    def _monitor_session(self, folder_id: str, driver) -> None:
        try:
            while True:
                try:
                    _ = driver.window_handles
                    time.sleep(1)
                except Exception:
                    break
        finally:
            with suppress(Exception):
                driver.quit()
            with self._session_lock:
                current = self._live_sessions.get(folder_id)
                if current is driver:
                    self._live_sessions.pop(folder_id, None)

    def _create_driver(self, options):
        try:
            return webdriver.Chrome(options=options)
        except Exception as ex:
            if "session not created" in str(ex).lower() and "extension" in str(ex).lower():
                options.extensions = []
                return webdriver.Chrome(options=options)
            raise

    def _webrtc_block_script(self) -> str:
        return (
            "(()=>{"
            "const undef=()=>undefined;"
            "try{Object.defineProperty(window,'RTCPeerConnection',{get:undef,configurable:true});}catch(e){}"
            "try{Object.defineProperty(window,'webkitRTCPeerConnection',{get:undef,configurable:true});}catch(e){}"
            "try{Object.defineProperty(navigator,'mediaDevices',{get:()=>undefined,configurable:true});}catch(e){}"
            "try{Object.defineProperty(window,'RTCDataChannel',{get:undef,configurable:true});}catch(e){}"
            "})();"
        )

    def _apply_spoof(self, driver, identity_settings: Dict, identity_bundle: Dict, launch_result: Dict):
        webdriver_script = "(()=>{try{delete Object.getPrototypeOf(navigator).webdriver}catch(e){}})();"
        scripts = [webdriver_script]

        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": webdriver_script})
        except Exception as exc:
            self._set_step_status(launch_result, "webdriver_masking", False, "webdriver masking", exc)
        else:
            self._set_step_status(launch_result, "webdriver_masking", True)

        if identity_settings.get("webrtc_disabled"):
            webrtc_script = self._webrtc_block_script()
            scripts.append(webrtc_script)
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": webrtc_script})
            except Exception as exc:
                self._set_step_status(launch_result, "webrtc_setup", False, "WebRTC setup", exc)
            else:
                self._set_step_status(launch_result, "webrtc_setup", True)
        else:
            self._set_step_status(launch_result, "webrtc_setup", None)

        tz_raw = identity_settings.get("timezone")
        tz_override = TIME_ZONE_MAP.get(tz_raw, tz_raw) if tz_raw else None

        locale_raw = identity_settings.get("language")
        locale_override = LANG_CODE_MAP.get(locale_raw, locale_raw) if locale_raw else None

        ua_metadata = identity_bundle.get("ua_metadata")
        override_params = {
            "userAgent": identity_bundle["user_agent"],
            "platform": identity_bundle["navigator_platform"],
        }
        if ua_metadata:
            override_params["userAgentMetadata"] = ua_metadata
        if locale_override:
            override_params["acceptLanguage"] = locale_override

        try:
            driver.execute_cdp_cmd("Network.setUserAgentOverride", override_params)
        except Exception as exc:
            self._set_step_status(launch_result, "user_agent_override", False, "user-agent override", exc)
            if ua_metadata:
                self._set_step_status(launch_result, "ua_metadata_override", False, "UA metadata", exc)
            else:
                self._set_step_status(launch_result, "ua_metadata_override", None)
        else:
            self._set_step_status(launch_result, "user_agent_override", True)
            if ua_metadata:
                self._set_step_status(launch_result, "ua_metadata_override", True)
            else:
                self._set_step_status(launch_result, "ua_metadata_override", None)

        if tz_override:
            try:
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": tz_override})
            except Exception as exc:
                self._set_step_status(launch_result, "timezone_override", False, "time zone", exc)
            else:
                self._set_step_status(launch_result, "timezone_override", True)
        else:
            self._set_step_status(launch_result, "timezone_override", None)

        if locale_override:
            try:
                driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": locale_override})
            except Exception as exc:
                self._set_step_status(launch_result, "locale_override", False, "language/locale", exc)
            else:
                self._set_step_status(launch_result, "locale_override", True)
        else:
            self._set_step_status(launch_result, "locale_override", None)

        geolocation_enabled = identity_settings.get("geolocation_enabled")
        geolocation_mode = None
        if geolocation_enabled is False:
            geolocation_mode = "block"
            try:
                # Empty params intentionally means "position unavailable" in CDP.
                driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {})
            except Exception as exc:
                self._set_step_status(launch_result, "geolocation_behavior", False, "geolocation handling", exc)
            else:
                self._set_step_status(launch_result, "geolocation_behavior", True)
        elif geolocation_enabled is True:
            geolocation_mode = "clear"
            try:
                driver.execute_cdp_cmd("Emulation.clearGeolocationOverride", {})
            except Exception as exc:
                self._set_step_status(launch_result, "geolocation_behavior", False, "geolocation handling", exc)
            else:
                self._set_step_status(launch_result, "geolocation_behavior", True)
        else:
            self._set_step_status(launch_result, "geolocation_behavior", None)

        try:
            driver.execute_cdp_cmd(
                "Target.setAutoAttach",
                {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True},
            )
        except Exception as exc:
            self._set_step_status(
                launch_result,
                "target_propagation",
                False,
                "child target propagation",
                exc,
            )
        else:
            self._recurse_existing_targets(
                driver,
                identity_bundle,
                tz_override,
                locale_override,
                scripts,
                geolocation_mode,
                launch_result,
            )

    def _send_target_message(self, driver, session_id: str, message_id: int, method: str, params: Optional[Dict] = None) -> int:
        driver.execute_cdp_cmd(
            "Target.sendMessageToTarget",
            {
                "sessionId": session_id,
                "message": json.dumps(
                    {
                        "id": message_id,
                        "method": method,
                        "params": params or {},
                    }
                ),
            },
        )
        return message_id + 1

    def _recurse_existing_targets(
        self,
        driver,
        identity_bundle: Dict,
        tz_override,
        locale_override,
        scripts,
        geolocation_mode,
        launch_result: Dict,
    ):
        page_like_types = {"page", "iframe", "sub_frame"}
        worker_types = {"worker", "service_worker", "shared_worker"}
        allowed = page_like_types | worker_types
        skip = ("chrome://", "devtools://", "about:", "edge://")

        try:
            target_infos = driver.execute_cdp_cmd("Target.getTargets", {}).get("targetInfos", [])
        except Exception as exc:
            self._set_step_status(
                launch_result,
                "target_propagation",
                False,
                "child target propagation",
                exc,
            )
            return

        eligible_targets = [
            target
            for target in target_infos
            if target.get("type") in allowed and not target.get("url", "").startswith(skip)
        ]

        # Auto-attach succeeded, and there are no current extra targets to patch.
        if not eligible_targets:
            self._set_step_status(launch_result, "target_propagation", True)
            return

        target_errors = []

        for target in eligible_targets:
            session_id = None
            target_type = target.get("type", "target")
            try:
                session_id = driver.execute_cdp_cmd(
                    "Target.attachToTarget",
                    {"targetId": target["targetId"], "flatten": True},
                )["sessionId"]

                message_id = 1

                if target_type in page_like_types:
                    for script in scripts:
                        message_id = self._send_target_message(
                            driver,
                            session_id,
                            message_id,
                            "Page.addScriptToEvaluateOnNewDocument",
                            {"source": script},
                        )

                ua_params = {
                    "userAgent": identity_bundle["user_agent"],
                    "platform": identity_bundle["navigator_platform"],
                }
                if identity_bundle.get("ua_metadata"):
                    ua_params["userAgentMetadata"] = identity_bundle["ua_metadata"]
                if locale_override:
                    ua_params["acceptLanguage"] = locale_override

                message_id = self._send_target_message(
                    driver,
                    session_id,
                    message_id,
                    "Network.setUserAgentOverride",
                    ua_params,
                )

                if target_type in page_like_types and tz_override:
                    message_id = self._send_target_message(
                        driver,
                        session_id,
                        message_id,
                        "Emulation.setTimezoneOverride",
                        {"timezoneId": tz_override},
                    )

                if target_type in page_like_types and locale_override:
                    message_id = self._send_target_message(
                        driver,
                        session_id,
                        message_id,
                        "Emulation.setLocaleOverride",
                        {"locale": locale_override},
                    )

                if target_type in page_like_types and geolocation_mode == "block":
                    message_id = self._send_target_message(
                        driver,
                        session_id,
                        message_id,
                        "Emulation.setGeolocationOverride",
                        {},
                    )

                if target_type in page_like_types and geolocation_mode == "clear":
                    message_id = self._send_target_message(
                        driver,
                        session_id,
                        message_id,
                        "Emulation.clearGeolocationOverride",
                        {},
                    )
            except Exception as exc:
                target_errors.append(f"{target_type}: {self._short_error(exc)}")
            finally:
                if session_id:
                    with suppress(Exception):
                        driver.execute_cdp_cmd("Target.detachFromTarget", {"sessionId": session_id})

        if target_errors:
            summary = target_errors[0]
            if len(target_errors) > 1:
                summary = f"{summary} (+{len(target_errors) - 1} more)"
            self._set_step_status(
                launch_result,
                "target_propagation",
                False,
                "child target propagation",
                summary,
            )
        else:
            self._set_step_status(launch_result, "target_propagation", True)
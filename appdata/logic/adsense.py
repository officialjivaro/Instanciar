# appdata/logic/adsense.py
import os, random, hashlib, json, secrets
from PySide6.QtCore import QUrl, QTimer, QObject
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from appdata.utils.random_user_agent import generate_random_user_agent


_LOCALES = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ru-RU", "ja-JP", "ko-KR", "pt-BR"]
_PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]


def _choose_persona():
    ua = generate_random_user_agent()
    locale = random.choice(_LOCALES)
    platform = random.choice(_PLATFORMS)
    return dict(ua=ua, accept=locale, platform=platform, vp=(728, 90), dpr=1, plugins=["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"], canvasSalt=secrets.token_hex(4))


_PERSONA = _choose_persona()


def _profile():
    tag = hashlib.sha256(_PERSONA["ua"].encode()).hexdigest()[:8]
    prof = QWebEngineProfile(f"ads_profile_{tag}")
    prof.setHttpUserAgent(_PERSONA["ua"])
    if hasattr(prof, "setHttpAcceptLanguage"):
        prof.setHttpAcceptLanguage(_PERSONA["accept"])
    prof.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
    prof.setPersistentStoragePath("")
    return prof


_STEALTH_JS = f"""
(()=>{{const d=z=>({{get:()=>z,configurable:true}}));
Object.defineProperty(navigator,'webdriver',d(undefined));
Object.defineProperty(navigator,'platform',d('{_PERSONA["platform"]}'));
Object.defineProperty(navigator,'language',d('{_PERSONA["accept"]}'));
Object.defineProperty(navigator,'languages',d(['{_PERSONA["accept"]}']));
Object.defineProperty(navigator,'plugins',d({json.dumps(_PERSONA["plugins"])}));
Object.defineProperty(screen,'width',d({_PERSONA["vp"][0]}));
Object.defineProperty(screen,'height',d({_PERSONA["vp"][1]}));
Object.defineProperty(window,'devicePixelRatio',d({_PERSONA["dpr"]}));
const o={int(_PERSONA["canvasSalt"][:2],16)};
const t=HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL=function(){{const c=this.getContext('2d');if(c){{c.fillStyle='rgba(0,0,0,0.01)';c.fillRect(o,o,1,1);}}return t.apply(this,arguments);}};
}})();
"""

_AD_HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4223077320283786" crossorigin="anonymous"></script></head><body style="background:#323232;margin:0;text-align:center;"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-4223077320283786" data-ad-slot="7522220612"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></body></html>
"""


class _AdPage(QWebEnginePage):
    def acceptNavigationRequest(self, u, t, m):
        if t == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(u)
            return False
        return super().acceptNavigationRequest(u, t, m)

    def javaScriptConsoleMessage(self, level, message, line, source):
        if "googleads.g.doubleclick.net" in source or "googlesyndication" in source:
            return
        super().javaScriptConsoleMessage(level, message, line, source)


def _install_scripts(page):
    sc = QWebEngineScript()
    sc.setName("stealth")
    inj = getattr(QWebEngineScript, "DocumentStart", QWebEngineScript.DocumentReady)
    sc.setInjectionPoint(inj)
    sc.setRunsOnSubFrames(True)
    sc.setWorldId(QWebEngineScript.MainWorld)
    sc.setSourceCode(_STEALTH_JS)
    page.profile().scripts().insert(sc)


def _simulate_behaviour(view):
    page = view.page()

    def step(i=0):
        if i > 2:
            return
        page.runJavaScript("window.dispatchEvent(new MouseEvent('mousemove',{clientX:10,clientY:10}));")
        QTimer.singleShot(400 + i * 200, lambda: step(i + 1))

    step()


class _Once(QObject):
    def __init__(self, v):
        super().__init__(v)
        v.loadFinished.connect(lambda ok: self.onload(v, ok))

    def onload(self, v, ok):
        if ok:
            _simulate_behaviour(v)
            v.loadFinished.disconnect()


def create_adsense_view():
    view = QWebEngineView()
    view.setFixedSize(728, 90)
    prof = _profile()
    prof.setParent(view)
    view._ads_profile = prof
    pg = _AdPage(prof, view)
    view.setPage(pg)
    _install_scripts(pg)
    _Once(view)
    return view


def load_adsense_content(view):
    view.setHtml(_AD_HTML, QUrl("https://jivaro.net/"))

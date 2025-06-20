# appdata/logic/proxy_tester.py
import socket, concurrent.futures
from PySide6.QtCore import QObject, Signal

class ProxyTester(QObject):
    result = Signal(str, bool)                  # instance name, ok?

    def __init__(self):
        super().__init__()
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)

    def test(self, name: str, host: str, port: str, timeout: int = 3):
        self._pool.submit(self._probe, name, host, port, timeout)

    def _probe(self, name, host, port, timeout):
        ok = False
        try:
            s = socket.create_connection((host, int(port)), timeout=timeout)
            s.close()
            ok = True
        except Exception:
            ok = False
        self.result.emit(name, ok)

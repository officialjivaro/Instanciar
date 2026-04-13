# appdata/logic/proxy_tester.py
import base64
import concurrent.futures
import socket
import ssl
import struct

from PySide6.QtCore import QObject, Signal


class ProxyTester(QObject):
    """Asynchronous proxy tester that follows the saved proxy protocol/auth settings."""

    result = Signal(str, str, bool, str)  # instance name, request id, ok, reason

    _HTTP_TARGET_HOST = "example.com"
    _HTTP_TARGET_PORT = 443
    _SOCKS4_TARGET_IP = "1.1.1.1"
    _SOCKS4_TARGET_PORT = 443

    def __init__(self):
        super().__init__()
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)

    def test(
        self,
        name: str,
        request_id: str,
        host: str,
        port: str,
        protocol: str,
        auth_enabled: bool = False,
        user: str = "",
        password: str = "",
        timeout: int = 3,
    ):
        self._pool.submit(
            self._probe,
            name,
            request_id,
            host,
            port,
            protocol,
            auth_enabled,
            user,
            password,
            timeout,
        )

    def _probe(self, name, request_id, host, port, protocol, auth_enabled, user, password, timeout):
        ok = False
        reason = ""

        try:
            host = (host or "").strip()
            port_text = (port or "").strip()
            protocol_name = (protocol or "HTTP").strip().upper()
            username = (user or "").strip()
            proxy_password = (password or "").strip()

            if not host:
                raise ValueError("Proxy host is blank.")
            if not port_text.isdigit():
                raise ValueError("Proxy port is invalid.")

            port_number = int(port_text)
            if port_number < 1 or port_number > 65535:
                raise ValueError("Proxy port is out of range.")

            if protocol_name == "HTTP":
                ok, reason = self._test_http_proxy(host, port_number, auth_enabled, username, proxy_password, timeout)
            elif protocol_name == "HTTPS":
                ok, reason = self._test_https_proxy(host, port_number, auth_enabled, username, proxy_password, timeout)
            elif protocol_name == "SOCKS5":
                ok, reason = self._test_socks5_proxy(host, port_number, auth_enabled, username, proxy_password, timeout)
            elif protocol_name == "SOCKS4":
                ok, reason = self._test_socks4_proxy(host, port_number, auth_enabled, username, timeout)
            else:
                ok, reason = False, f"Unsupported proxy protocol: {protocol_name}."
        except Exception as exc:
            ok = False
            reason = self._short_error(exc)

        self.result.emit(name, request_id, ok, reason)

    def _open_socket(self, host, port, timeout):
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(timeout)
        return sock

    def _http_connect_request(self, auth_enabled, user, password):
        auth_header = ""
        if auth_enabled:
            token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
            auth_header = f"Proxy-Authorization: Basic {token}\r\n"

        request = (
            f"CONNECT {self._HTTP_TARGET_HOST}:{self._HTTP_TARGET_PORT} HTTP/1.1\r\n"
            f"Host: {self._HTTP_TARGET_HOST}:{self._HTTP_TARGET_PORT}\r\n"
            "Proxy-Connection: close\r\n"
            f"{auth_header}\r\n"
        )
        return request.encode("ascii")

    def _read_http_status(self, sock):
        with sock.makefile("rb") as stream:
            status_line = stream.readline(4096).decode("iso-8859-1", errors="replace").strip()

        if not status_line:
            return None, "No response from proxy."

        parts = status_line.split(" ", 2)
        if len(parts) < 2 or not parts[1].isdigit():
            return None, f"Unexpected proxy response: {status_line}"

        return int(parts[1]), status_line

    def _http_result_from_status(self, status_code):
        if status_code == 200:
            return True, ""
        if status_code == 407:
            return False, "Proxy authentication failed or is required."
        if status_code == 403:
            return False, "Proxy refused the tunnel request."
        if 400 <= status_code < 500:
            return False, f"Proxy request was rejected ({status_code})."
        if 500 <= status_code < 600:
            return False, f"Proxy server error ({status_code})."
        return False, f"Unexpected proxy response ({status_code})."

    def _test_http_proxy(self, host, port, auth_enabled, user, password, timeout):
        with self._open_socket(host, port, timeout) as sock:
            sock.sendall(self._http_connect_request(auth_enabled, user, password))
            status_code, status_line = self._read_http_status(sock)
            if status_code is None:
                return False, status_line
            return self._http_result_from_status(status_code)

    def _test_https_proxy(self, host, port, auth_enabled, user, password, timeout):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with self._open_socket(host, port, timeout) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=host) as tls_sock:
                tls_sock.sendall(self._http_connect_request(auth_enabled, user, password))
                status_code, status_line = self._read_http_status(tls_sock)
                if status_code is None:
                    return False, status_line
                return self._http_result_from_status(status_code)

    def _recv_exact(self, sock, size):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise OSError("Proxy closed the connection unexpectedly.")
            data += chunk
        return data

    def _test_socks5_proxy(self, host, port, auth_enabled, user, password, timeout):
        with self._open_socket(host, port, timeout) as sock:
            methods = b"\x02" if auth_enabled else b"\x00"
            sock.sendall(b"\x05\x01" + methods)
            greeting = self._recv_exact(sock, 2)

            if greeting[0] != 0x05:
                return False, "Invalid SOCKS5 handshake response."

            method = greeting[1]
            if method == 0xFF:
                return False, "SOCKS5 proxy rejected the requested authentication method."

            if auth_enabled:
                if method != 0x02:
                    return False, "SOCKS5 proxy did not accept username/password authentication."
                auth_reply = self._socks5_auth(sock, user, password)
                if auth_reply != 0x00:
                    return False, "SOCKS5 username/password authentication failed."
            else:
                if method != 0x00:
                    return False, "SOCKS5 proxy requires authentication."

            target = self._HTTP_TARGET_HOST.encode("ascii")
            request = b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", self._HTTP_TARGET_PORT)
            sock.sendall(request)

            response_head = self._recv_exact(sock, 4)
            if response_head[0] != 0x05:
                return False, "Invalid SOCKS5 connect response."

            reply_code = response_head[1]
            if reply_code != 0x00:
                return False, self._socks5_reply_message(reply_code)

            self._discard_socks5_bound_address(sock, response_head[3])
            return True, ""

    def _socks5_auth(self, sock, user, password):
        username = user.encode("utf-8")
        proxy_password = password.encode("utf-8")

        if len(username) > 255 or len(proxy_password) > 255:
            raise ValueError("SOCKS5 username/password is too long.")

        request = (
            b"\x01"
            + bytes([len(username)])
            + username
            + bytes([len(proxy_password)])
            + proxy_password
        )
        sock.sendall(request)
        reply = self._recv_exact(sock, 2)

        if reply[0] != 0x01:
            raise OSError("Invalid SOCKS5 auth response.")

        return reply[1]

    def _discard_socks5_bound_address(self, sock, atyp):
        if atyp == 0x01:  # IPv4
            self._recv_exact(sock, 4 + 2)
        elif atyp == 0x03:  # domain
            length = self._recv_exact(sock, 1)[0]
            self._recv_exact(sock, length + 2)
        elif atyp == 0x04:  # IPv6
            self._recv_exact(sock, 16 + 2)
        else:
            raise OSError("Invalid SOCKS5 address type in response.")

    def _socks5_reply_message(self, code):
        messages = {
            0x01: "SOCKS5 general server failure.",
            0x02: "SOCKS5 connection was blocked by rules.",
            0x03: "SOCKS5 network unreachable.",
            0x04: "SOCKS5 host unreachable.",
            0x05: "SOCKS5 connection refused by destination.",
            0x06: "SOCKS5 TTL expired.",
            0x07: "SOCKS5 command is not supported.",
            0x08: "SOCKS5 address type is not supported.",
        }
        return messages.get(code, f"SOCKS5 proxy rejected the connection ({code}).")

    def _test_socks4_proxy(self, host, port, auth_enabled, user, timeout):
        with self._open_socket(host, port, timeout) as sock:
            user_id = user.encode("utf-8") if auth_enabled and user else b""
            if b"\x00" in user_id:
                raise ValueError("SOCKS4 username cannot contain null characters.")

            request = (
                b"\x04\x01"
                + struct.pack(">H", self._SOCKS4_TARGET_PORT)
                + socket.inet_aton(self._SOCKS4_TARGET_IP)
                + user_id
                + b"\x00"
            )
            sock.sendall(request)
            reply = self._recv_exact(sock, 8)

            if reply[0] not in (0x00, 0x04):
                return False, "Invalid SOCKS4 response."

            status = reply[1]
            if status == 0x5A:
                return True, ""
            if status == 0x5B:
                return False, "SOCKS4 request was rejected."
            if status == 0x5C:
                return False, "SOCKS4 proxy could not reach the destination."
            if status == 0x5D:
                return False, "SOCKS4 user ID could not be verified."

            return False, f"SOCKS4 proxy rejected the connection ({status})."

    def _short_error(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        if len(message) > 140:
            return message[:137] + "..."
        return message
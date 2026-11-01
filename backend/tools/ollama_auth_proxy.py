"""Reverse proxy đặt trước Ollama để thêm xác thực bearer token.

Ollama không có cơ chế xác thực nào, nên nó chỉ được nghe trên 127.0.0.1.
Proxy này nghe ra ngoài mạng, kiểm tra token rồi mới chuyển tiếp vào Ollama.

Chạy trên máy có Ollama:

    set OLLAMA_PROXY_TOKEN=<token>
    python ollama_auth_proxy.py --listen 0.0.0.0:11435

Client gọi kèm header: Authorization: Bearer <token>
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import socket
import socketserver
import sys
import urllib.error
import urllib.request
from hmac import compare_digest

UPSTREAM = os.environ.get("OLLAMA_UPSTREAM", "http://127.0.0.1:11434")
TOKEN = os.environ.get("OLLAMA_PROXY_TOKEN", "")

# Chỉ cho phép các endpoint đọc/suy luận. Các route huỷ dữ liệu như
# DELETE /api/delete hay POST /api/pull đều không nằm trong danh sách này.
ALLOWED = {
    ("POST", "/api/chat"),
    ("POST", "/api/generate"),
    ("POST", "/api/embed"),
    ("POST", "/api/embeddings"),
    ("POST", "/api/show"),
    ("GET", "/api/tags"),
    ("GET", "/api/ps"),
    ("GET", "/api/version"),
}

# Header hop-by-hop không được chuyển tiếp (RFC 7230 §6.1).
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}

MAX_BODY = 32 * 1024 * 1024  # 32 MB, đủ cho ảnh base64 của model vision


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ollama-auth-proxy"
    sys_version = ""

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_cors(self) -> None:
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        scheme, _, value = header.partition(" ")
        if scheme.lower() != "bearer":
            return False
        # compare_digest tránh rò rỉ thông tin qua thời gian so sánh
        return compare_digest(value.strip(), TOKEN)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._send_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._proxy("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._proxy("POST")

    def _proxy(self, method: str) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return

        if not self._authorized():
            # Không nói rõ token sai hay thiếu, tránh giúp người dò
            self._send_json(401, {"error": "unauthorized"})
            return

        if (method, path) not in ALLOWED:
            self._send_json(403, {"error": f"endpoint not allowed: {method} {path}"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._send_json(413, {"error": "body too large"})
            return
        body = self.rfile.read(length) if length else None

        req = urllib.request.Request(
            UPSTREAM + self.path,
            data=body,
            method=method,
            headers={"Content-Type": self.headers.get("Content-Type", "application/json")},
        )

        try:
            with urllib.request.urlopen(req, timeout=600) as upstream:
                self._relay(upstream)
        except urllib.error.HTTPError as e:
            self._relay(e)
        except urllib.error.URLError as e:
            self._send_json(502, {"error": f"upstream unreachable: {e.reason}"})
        except (BrokenPipeError, ConnectionResetError):
            pass  # client ngắt giữa chừng — không có gì để báo

    def _relay(self, upstream) -> None:
        """Chuyển tiếp response, phát trực tiếp theo luồng để stream hoạt động."""
        self.send_response(upstream.status)
        for key, value in upstream.headers.items():
            if key.lower() not in HOP_BY_HOP and key.lower() != "content-length":
                self.send_header(key, value)
        self.send_header("Transfer-Encoding", "chunked")
        self._send_cors()
        self.end_headers()

        while chunk := upstream.read(8192):
            self.wfile.write(b"%X\r\n%s\r\n" % (len(chunk), chunk))
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    address_family = socket.AF_INET


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen", default="0.0.0.0:11435", help="host:port để nghe")
    args = parser.parse_args()

    if not TOKEN:
        print("LOI: chua dat bien moi truong OLLAMA_PROXY_TOKEN", file=sys.stderr)
        return 1
    if len(TOKEN) < 16:
        print("LOI: OLLAMA_PROXY_TOKEN qua ngan, can it nhat 16 ky tu", file=sys.stderr)
        return 1

    host, _, port = args.listen.rpartition(":")

    with Server((host, int(port)), Handler) as httpd:
        print(f"proxy {args.listen} -> {UPSTREAM}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("dung", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import select
import socket
import sys
from urllib.parse import urlsplit


BUFFER = 65536


def relay(left, right):
    sockets = [left, right]
    try:
        while True:
            readable, _, _ = select.select(sockets, [], [], 60)
            if not readable:
                return
            for src in readable:
                data = src.recv(BUFFER)
                if not data:
                    return
                (right if src is left else left).sendall(data)
    finally:
        for sock in sockets:
            try:
                sock.close()
            except OSError:
                pass


def recv_headers(client):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = client.recv(BUFFER)
        if not chunk:
            break
        data += chunk
        if len(data) > 1024 * 1024:
            raise ValueError("headers too large")
    return data


def handle(client):
    try:
        data = recv_headers(client)
        if not data:
            return
        header, _, body = data.partition(b"\r\n\r\n")
        lines = header.decode("iso-8859-1").split("\r\n")
        method, target, version = lines[0].split(" ", 2)

        if method.upper() == "CONNECT":
            host, _, port_text = target.partition(":")
            port = int(port_text or "443")
            upstream = socket.create_connection((host, port), timeout=30)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            relay(client, upstream)
            return

        parsed = urlsplit(target)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        filtered = []
        for line in lines[1:]:
            if not line.lower().startswith(("proxy-connection:", "connection:")):
                filtered.append(line)
        request = f"{method} {path} {version}\r\n" + "\r\n".join(filtered) + "\r\nConnection: close\r\n\r\n"

        upstream = socket.create_connection((host, port), timeout=30)
        upstream.sendall(request.encode("iso-8859-1") + body)
        relay(client, upstream)
    except Exception as exc:
        try:
            client.sendall(f"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n{exc}\n".encode())
        except OSError:
            pass
        try:
            client.close()
        except OSError:
            pass


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3128
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(128)
    print(f"proxy listening on {host}:{port}", flush=True)
    while True:
        client, _ = server.accept()
        pid = None
        try:
            pid = __import__("os").fork()
        except AttributeError:
            pid = None
        if pid == 0:
            server.close()
            handle(client)
            sys.exit(0)
        client.close()


if __name__ == "__main__":
    main()

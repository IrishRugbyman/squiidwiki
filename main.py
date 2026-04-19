import os
import socket

import uvicorn

from backend.server import app
from backend.settings import settings


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    port = start_port
    attempts = 0
    while is_port_in_use(port) and attempts < max_attempts:
        port += 1
        attempts += 1
    return port


if __name__ == "__main__":
    if settings.is_development():
        os.system("tree /F /A > project_tree.txt")

    port = find_available_port(settings.server.port)
    if port != settings.server.port:
        print(f"Port {settings.server.port} is in use. Using port {port}.")

    print("Starting server")
    uvicorn.run(app, host=settings.server.host, port=port)

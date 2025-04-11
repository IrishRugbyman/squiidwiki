import os
import sys
import socket
import uvicorn

from backend.server import app
from backend.config.config import settings


def is_port_in_use(port: int) -> bool:
    """
    Check if a port is already in use.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """
    Find an available port starting from start_port.
    """
    port = start_port
    attempts = 0
    while is_port_in_use(port) and attempts < max_attempts:
        port += 1
        attempts += 1
    return port


if __name__ == "__main__":
    # Skip database initialization
    
    # Generate project tree if requested
    if settings.DEBUG:
        os.system("tree /F /A > project_tree.txt")
        print("Project tree saved to project_tree.txt")
    
    # Find an available port (handle the case where the default port is in use)
    port = find_available_port(settings.PORT)
    if port != settings.PORT:
        print(f"Port {settings.PORT} is already in use. Using port {port} instead.")
    
    # Start the server
    print(f"Starting server")
    uvicorn.run(app, host=settings.HOST, port=port)

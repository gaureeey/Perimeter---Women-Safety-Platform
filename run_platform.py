
import os
import sys
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

backend_process = None
frontend_process = None


def port_is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_backend():
    global backend_process

    if port_is_open(8000):
        print("Backend already responds on port 8000.")
        return

    if not (BACKEND_DIR / "app" / "main.py").exists():
        raise FileNotFoundError(
            f"Backend entry point not found in {BACKEND_DIR}"
        )

    print("Starting FastAPI backend on port 8000...")
    backend_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ],
        cwd=str(BACKEND_DIR),
    )


def start_frontend():
    global frontend_process

    if port_is_open(8080):
        print("A server is already responding on port 8080.")
        return

    # Prefer the existing Node.js frontend server if available.
    if (ROOT_DIR / "server.js").exists():
        try:
            subprocess.run(
                ["node", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            command = ["node", "server.js"]
        except (FileNotFoundError, subprocess.CalledProcessError):
            command = None
    else:
        command = None

    if command:
        print("Starting frontend with Node.js on port 8080...")
        frontend_process = subprocess.Popen(
            command, cwd=str(ROOT_DIR)
        )
    else:
        # Serve the frontend directory using Python.
        if not FRONTEND_DIR.exists():
            raise FileNotFoundError(
                f"Frontend directory not found: {FRONTEND_DIR}"
            )

        print("Starting frontend with Python on port 8080...")
        frontend_process = subprocess.Popen(
            [
                sys.executable, "-m", "http.server",
                "8080",
                "--bind", "127.0.0.1",
                "--directory", str(FRONTEND_DIR),
            ],
            cwd=str(ROOT_DIR),
        )


def stop_servers():
    for process in (frontend_process, backend_process):
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main():
    try:
        start_backend()
        start_frontend()

        # Wait briefly and detect early startup failures.
        for _ in range(10):
            if backend_process and backend_process.poll() is not None:
                raise RuntimeError("Backend stopped during startup.")
            if frontend_process and frontend_process.poll() is not None:
                raise RuntimeError("Frontend stopped during startup.")

            if port_is_open(8000) and port_is_open(8080):
                break
            time.sleep(1)

        print("\nPerimeter startup check:")
        print("Backend:  http://127.0.0.1:8000/docs")
        print("Frontend: http://127.0.0.1:8080/")
        print("\nPress Ctrl+C to stop servers started by this launcher.")

        if port_is_open(8080):
            webbrowser.open("http://127.0.0.1:8080/")

        while True:
            if backend_process and backend_process.poll() is not None:
                raise RuntimeError("Backend process exited.")
            if frontend_process and frontend_process.poll() is not None:
                raise RuntimeError("Frontend process exited.")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping Perimeter servers...")
    finally:
        stop_servers()


if __name__ == "__main__":
    main()

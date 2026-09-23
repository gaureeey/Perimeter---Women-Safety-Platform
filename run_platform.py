"""
PERIMETER Platform - Unified Master Launcher
Starts both the FastAPI Backend (Port 8000) and Frontend Server (Port 8080),
and opens the platform in your default browser.
"""
import sys
import os
import subprocess
import time
import socket
import webbrowser
from threading import Thread

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex((host, port)) == 0

def find_best_python():
    candidates = [
        sys.executable,
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Python", "bin", "python.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Python", "pythoncore-3.14-64", "python.exe"),
        "python",
        "py"
    ]
    for c in candidates:
        if os.path.isabs(c) and os.path.exists(c):
            return c
    return sys.executable

def start_backend():
    if is_port_in_use(8000):
        print("⚡ Port 8000 is already running (Backend active).")
        return None

    python_exe = find_best_python()
    print(f"🚀 Starting FastAPI backend on http://127.0.0.1:8000 using {os.path.basename(python_exe)}...")
    cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    proc = subprocess.Popen(cmd, cwd=BACKEND_DIR)
    return proc

def start_frontend():
    if is_port_in_use(8080):
        print("⚡ Port 8080 is already running (Frontend active).")
        return None

    # Check for node
    node_available = False
    try:
        subprocess.run(["node", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        node_available = True
    except Exception:
        pass

    if node_available and os.path.exists(os.path.join(ROOT_DIR, "server.js")):
        print("🌐 Starting Frontend server on http://localhost:8080 via Node.js...")
        proc = subprocess.Popen(["node", "server.js"], cwd=ROOT_DIR)
        return proc
    else:
        python_exe = find_best_python()
        print(f"🌐 Starting Frontend server on http://localhost:8080 via Python...")
        proc = subprocess.Popen([python_exe, "serve.py"], cwd=ROOT_DIR)
        return proc

def main():
    print("=" * 64)
    print("🛡️  PERIMETER — Women Safety & Emergency Dispatch Platform")
    print("=" * 64)

    backend_proc = start_backend()
    frontend_proc = start_frontend()

    # Wait for backend port to open
    retries = 15
    while retries > 0 and not is_port_in_use(8000):
        time.sleep(0.5)
        retries -= 1

    print("\n" + "=" * 64)
    print("✅ Platform is fully online and ready!")
    print("📝 Registration & Login: http://localhost:8080/register.html")
    print("👩 Citizen Dashboard:    http://localhost:8080/user.html")
    print("🙋 Volunteer Desk:       http://localhost:8080/volunteer.html")
    print("🚔 Police Command:       http://localhost:8080/police.html")
    print("📰 Press Desk:           http://localhost:8080/journalist.html")
    print("👑 Admin Portal:         http://localhost:8080/admin.html")
    print("📚 API Documentation:    http://127.0.0.1:8000/docs")
    print("=" * 64)
    print("Press CTRL+C anytime to stop all servers.\n")

    # Open browser
    try:
        webbrowser.open("http://localhost:8080/register.html")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down PERIMETER platform servers...")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()

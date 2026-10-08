"""
PERIMETER Platform - Quick Database Inspector Shortcut
Runs the database inspection utility directly from the root folder.
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    script_path = os.path.join(os.path.dirname(__file__), "backend", "scripts", "inspect_db.py")
    cmd = [sys.executable, script_path] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

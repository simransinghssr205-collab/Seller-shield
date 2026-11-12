"""Start the backend (port 5000) and the frontend (port 3000) together.

Run it with the project's own Python:
    Windows:    venv\\Scripts\\python.exe run.py
    Mac/Linux:  venv/bin/python run.py
Press Ctrl+C to stop both.
"""
import shutil
import subprocess
import sys
import time
import webbrowser

try:
    import flask  # noqa: F401
except ImportError:
    sys.exit(
        "Flask is not installed for this Python.\n"
        "Run with the project's Python: venv\\Scripts\\python.exe run.py"
    )

if not shutil.which("node"):
    sys.exit("Node.js not found. Install it from nodejs.org, then run this again.")

backend = subprocess.Popen([sys.executable, "-m", "backend.app"])
frontend = subprocess.Popen(["node", "server.js"], cwd="Frontend")

time.sleep(2)
webbrowser.open("http://localhost:3000")

try:
    backend.wait()
except KeyboardInterrupt:
    pass
finally:
    for process in (backend, frontend):
        process.terminate()

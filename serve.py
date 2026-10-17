"""Regenerate the demo data, then serve the dashboard and open it in the browser."""
import functools
import http.server
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

PORT = 8000
BASE = Path(__file__).resolve().parent

subprocess.run([sys.executable, str(BASE / "generate_and_reconcile.py")], check=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(BASE))
url = f"http://localhost:{PORT}/index.html"
with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
    print(f"Serving dashboard at {url} (press Ctrl+C to stop)")
    threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

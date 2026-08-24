"""Production-level guard for the site's privacy-preserving traffic analytics."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import shutil
import socket
import subprocess
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"Next.js exited before serving the site:\n{output}")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise AssertionError("Next.js did not become ready within 30 seconds")


def test_production_site_requests_vercel_analytics_script() -> None:
    """Removing Analytics from the root layout must break this release contract."""
    assert (FRONTEND / ".next").exists(), (
        "frontend build is absent; run npm run build in frontend/"
    )
    node = shutil.which("node")
    assert node, "Node.js is required to exercise the production site"

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            node,
            str(FRONTEND / "node_modules" / "next" / "dist" / "bin" / "next"),
            "start",
            "--hostname",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=FRONTEND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server(url, process)
        requested: list[str] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.on("request", lambda request: requested.append(request.url))
            page.goto(url, wait_until="networkidle")
            browser.close()

        assert any(
            request.endswith("/_vercel/insights/script.js") for request in requested
        ), "the production page did not request Vercel Web Analytics"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

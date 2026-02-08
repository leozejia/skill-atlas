#!/usr/bin/env python3
"""Local visual Skills manager for skills.sh top lists."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FALLBACK_SKILLS_IPS = [
    "64.239.109.193",
    "64.239.123.129",
]

ROOT_DIR = Path(__file__).resolve().parents[1]
UI_DIR = ROOT_DIR / "ui"
INSTALL_SCRIPT = ROOT_DIR / "tools" / "install-skills-top80.py"
AGENTS_DIR = Path.home() / ".agents" / "skills"
STATE_PATH = Path.home() / ".agents" / ".skills-sh-top80-state.json"
REPORT_PATH = Path.home() / ".agents" / ".skills-sh-top80-report.json"
LOG_PATH = Path.home() / ".agents" / ".skills-sh-top80.log"
JOB_PATH = Path.home() / ".agents" / ".skills-sh-top80-job.json"

JOB_PROCESS: subprocess.Popen | None = None


def run_cmd(cmd: list[str], timeout: int) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, (bytes, bytearray)) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, (bytes, bytearray)) else (exc.stderr or "")
        msg = stderr.strip() or f"timeout after {timeout}s"
        return 124, stdout.strip(), msg


def curl_fetch(url: str, timeout: int, resolve_ip: str | None = None, headers: list[str] | None = None) -> str:
    cmd = ["curl", "-fsSL", "--max-time", str(timeout)]
    if resolve_ip:
        cmd += ["--resolve", f"skills.sh:443:{resolve_ip}"]
    if headers:
        for header in headers:
            cmd += ["-H", header]
    cmd.append(url)
    rc, out, err = run_cmd(cmd, timeout=timeout)
    if rc != 0:
        raise RuntimeError(err or out or f"curl failed ({rc})")
    return out


def dig_ips() -> list[str]:
    if not shutil.which("dig"):
        return []
    rc, out, _ = run_cmd(["dig", "+short", "skills.sh", "@8.8.8.8"], timeout=5)
    if rc != 0:
        return []
    ips = []
    for line in out.splitlines():
        line = line.strip()
        if line and all(part.isdigit() and 0 <= int(part) <= 255 for part in line.split(".")):
            ips.append(line)
    return ips


def fetch_skills_json(view: str, limit: int, timeout: int) -> dict:
    url = f"https://skills.sh/api/skills?view={view}&limit={limit}"
    try:
        return json.loads(curl_fetch(url, timeout=timeout))
    except Exception:
        pass

    last_err = None
    ips = []
    for ip in dig_ips() + FALLBACK_SKILLS_IPS:
        if ip not in ips:
            ips.append(ip)
    for ip in ips:
        try:
            payload = curl_fetch(url, timeout=timeout, resolve_ip=ip)
            return json.loads(payload)
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Failed to fetch skills list: {last_err}")


def list_installed() -> list[str]:
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(
        entry.name
        for entry in AGENTS_DIR.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def job_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def load_job_state() -> dict:
    if not JOB_PATH.is_file():
        return {}
    try:
        return json.loads(JOB_PATH.read_text())
    except Exception:
        return {}


def save_job_state(state: dict) -> None:
    JOB_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOB_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def start_install_job(payload: dict) -> dict:
    global JOB_PROCESS

    if JOB_PROCESS and JOB_PROCESS.poll() is None:
        return {"status": "running"}

    limit = int(payload.get("limit", 80))
    view = payload.get("view", "all-time")
    resolve_missing = bool(payload.get("resolveMissing", True))
    refresh = bool(payload.get("refresh", False))
    time_budget = int(payload.get("timeBudget", 0))
    cmd_timeout = int(payload.get("cmdTimeout", 40))

    cmd = [
        str(sys.executable),
        str(INSTALL_SCRIPT),
        "--limit",
        str(limit),
        "--view",
        view,
        "--report",
        str(REPORT_PATH),
        "--state",
        str(STATE_PATH),
        "--cmd-timeout",
        str(cmd_timeout),
    ]
    if resolve_missing:
        cmd.append("--resolve-missing")
    if refresh:
        cmd.append("--refresh")
    if time_budget:
        cmd += ["--time-budget", str(time_budget)]

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(LOG_PATH, "a", encoding="utf-8")
    JOB_PROCESS = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)

    state = {
        "pid": JOB_PROCESS.pid,
        "startedAt": time.time(),
        "cmd": cmd,
        "log": str(LOG_PATH),
        "report": str(REPORT_PATH),
    }
    save_job_state(state)
    return {"status": "started", **state}


def load_report() -> dict | None:
    if not REPORT_PATH.is_file():
        return None
    try:
        return json.loads(REPORT_PATH.read_text())
    except Exception:
        return None


def tail_log(lines: int = 120) -> str:
    if not LOG_PATH.is_file():
        return ""
    data = LOG_PATH.read_text(errors="ignore").splitlines()
    return "\n".join(data[-lines:])


def path_payload() -> dict:
    return {
        "root": str(ROOT_DIR),
        "custom": str(ROOT_DIR / "custom"),
        "shared": str(ROOT_DIR / "shared"),
        "agents": str(AGENTS_DIR),
    }


class SkillsHandler(BaseHTTPRequestHandler):
    server_version = "SkillsUI/0.1"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, payload: str, status: int = 200, content_type: str = "text/plain") -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api_get(parsed)
            return

        if parsed.path in ("/", ""):
            self._send_file(UI_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/style.css":
            self._send_file(UI_DIR / "style.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._send_file(UI_DIR / "app.js", "application/javascript; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_api_get(self, parsed) -> None:
        if parsed.path == "/api/summary":
            params = parse_qs(parsed.query)
            limit = int(params.get("limit", [80])[0])
            view = params.get("view", ["all-time"])[0]
            try:
                skills_data = fetch_skills_json(view=view, limit=limit, timeout=20)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=502)
                return

            installed = list_installed()
            installed_set = set(installed)
            skills = []
            for item in skills_data.get("skills", []):
                skill_id = item.get("id")
                status = "installed" if skill_id in installed_set else "missing"
                skills.append({**item, "status": status})

            installed_top = sum(1 for s in skills if s["status"] == "installed")
            payload = {
                "view": view,
                "limit": limit,
                "skills": skills,
                "installed": installed,
                "counts": {
                    "installedTotal": len(installed),
                    "installedTop": installed_top,
                    "missingTop": max(0, len(skills) - installed_top),
                },
            }
            self._send_json(payload)
            return

        if parsed.path == "/api/job":
            state = load_job_state()
            pid = state.get("pid")
            running = job_running(pid)
            exit_code = None
            global JOB_PROCESS
            if JOB_PROCESS:
                exit_code = JOB_PROCESS.poll()
                if exit_code is not None:
                    JOB_PROCESS = None
            payload = {**state, "running": running, "exitCode": exit_code}
            self._send_json(payload)
            return

        if parsed.path == "/api/report":
            report = load_report()
            if not report:
                self._send_json({"error": "report not found"}, status=404)
                return
            self._send_json(report)
            return

        if parsed.path == "/api/log":
            params = parse_qs(parsed.query)
            lines = int(params.get("lines", [120])[0])
            self._send_text(tail_log(lines), content_type="text/plain")
            return

        if parsed.path == "/api/paths":
            self._send_json(path_payload())
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/install":
            payload = self._parse_json_body()
            result = start_install_job(payload)
            self._send_json(result)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill-Atlas Visual Skills Manager")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5199)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), SkillsHandler)
    print(f"Skills UI running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

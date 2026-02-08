#!/usr/bin/env python3
"""Install top skills from skills.sh into ~/.agents/skills and link to agents."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

FALLBACK_SKILLS_IPS = [
    "64.239.109.193",
    "64.239.123.129",
]

DEFAULT_INSTALLER = os.path.expanduser(
    "~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py"
)


def run_cmd(cmd: List[str], timeout: int) -> Tuple[int, str, str]:
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


def curl_fetch(
    url: str,
    timeout: int,
    resolve_ip: Optional[str] = None,
    headers: Optional[List[str]] = None,
) -> str:
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


def dig_ips() -> List[str]:
    if not shutil.which("dig"):
        return []
    try:
        rc, out, _ = run_cmd(
            ["dig", "+short", "skills.sh", "@8.8.8.8"], timeout=5
        )
    except Exception:
        return []
    if rc != 0:
        return []
    ips = []
    for line in out.splitlines():
        line = line.strip()
        if line and all(part.isdigit() and 0 <= int(part) <= 255 for part in line.split(".")):
            ips.append(line)
    return ips


def fetch_skills_json(view: str, limit: int, timeout: int) -> Dict:
    url = f"https://skills.sh/api/skills?view={view}&limit={limit}"
    # Try direct first
    try:
        return json.loads(curl_fetch(url, timeout=timeout))
    except Exception:
        pass

    # Fallback to DNS override
    ips = []
    for ip in dig_ips() + FALLBACK_SKILLS_IPS:
        if ip not in ips:
            ips.append(ip)
    last_err = None
    for ip in ips:
        try:
            payload = curl_fetch(url, timeout=timeout, resolve_ip=ip)
            return json.loads(payload)
        except Exception as exc:
            last_err = exc
            continue
    raise RuntimeError(f"Failed to fetch skills list: {last_err}")


def github_json(url: str, timeout: int, token: Optional[str]) -> Dict:
    headers = ["Accept: application/vnd.github+json"]
    if token:
        headers.append(f"Authorization: token {token}")
    payload = curl_fetch(url, timeout=timeout, headers=headers)
    return json.loads(payload)


def is_branch_error(err: str) -> bool:
    err_lower = err.lower()
    return (
        "remote branch" in err_lower
        or "remote ref" in err_lower
        or "couldn't find remote ref" in err_lower
        or "not found in upstream" in err_lower
    )


def is_path_error(err: str) -> bool:
    err_lower = err.lower()
    return "skill path not found" in err_lower or "skill.md not found" in err_lower


def candidate_paths(skill_id: str) -> List[str]:
    return [
        f"skills/{skill_id}",
        f"skill/{skill_id}",
        f"plugins/{skill_id}",
        f"skills/.curated/{skill_id}",
        f"skills/curated/{skill_id}",
        f".curated/{skill_id}",
        f"skills/public/{skill_id}",
        f"skills/private/{skill_id}",
        skill_id,
    ]


def pick_best_path(paths: List[str], skill_id: str) -> Optional[str]:
    if not paths:
        return None
    skill_lower = skill_id.lower()
    exact = [p for p in paths if os.path.basename(p).lower() == skill_lower]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return sorted(exact, key=len)[0]
    segment = [p for p in paths if f"/{skill_lower}" in f"/{p.lower()}" or p.lower().endswith(skill_lower)]
    if len(segment) == 1:
        return segment[0]
    if len(segment) > 1:
        return sorted(segment, key=len)[0]
    if len(paths) == 1:
        return paths[0]
    return sorted(paths, key=len)[0]


def discover_path_via_tree(
    owner: str,
    repo: str,
    skill_id: str,
    ref: str,
    token: Optional[str],
    timeout: int,
    tree_cache: Dict[str, List[str]],
) -> Optional[str]:
    cache_key = f"{owner}/{repo}@{ref}"
    if cache_key not in tree_cache:
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
        data = github_json(url, timeout=timeout, token=token)
        tree_cache[cache_key] = [
            entry.get("path")
            for entry in data.get("tree", [])
            if entry.get("type") == "blob" and entry.get("path", "").endswith("/SKILL.md")
        ]
    candidates = [p[:-len("/SKILL.md")] for p in tree_cache[cache_key] if p]
    return pick_best_path(candidates, skill_id)


def install_skill(
    installer: str,
    repo: str,
    path: str,
    ref: str,
    dest: str,
    method: str,
    timeout: int,
) -> Tuple[int, str, str]:
    cmd = [
        sys.executable,
        installer,
        "--repo",
        repo,
        "--path",
        path,
        "--dest",
        dest,
        "--method",
        method,
        "--ref",
        ref,
    ]
    return run_cmd(cmd, timeout=timeout)


def ensure_symlink(target: str, link_dir: str) -> None:
    if not link_dir or not os.path.isdir(link_dir):
        return
    link_path = os.path.join(link_dir, os.path.basename(target))
    if os.path.lexists(link_path):
        return
    os.symlink(target, link_path)


def load_state(path: str) -> Dict:
    if not os.path.isfile(path):
        return {"skip_ids": [], "path_cache": {}}
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"skip_ids": [], "path_cache": {}}
        data.setdefault("skip_ids", [])
        data.setdefault("path_cache", {})
        return data
    except Exception:
        return {"skip_ids": [], "path_cache": {}}


def save_state(path: str, state: Dict) -> None:
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install top skills from skills.sh")
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--view", default="all-time", choices=["all-time", "trending", "hot"])
    parser.add_argument("--dest", default=os.path.expanduser("~/.agents/skills"))
    parser.add_argument("--installer", default=DEFAULT_INSTALLER)
    parser.add_argument("--method", default="git", choices=["auto", "download", "git"])
    parser.add_argument("--timeout", type=int, default=30, help="curl timeout in seconds")
    parser.add_argument("--cmd-timeout", type=int, default=40, help="install command timeout")
    parser.add_argument("--time-budget", type=int, default=0, help="stop after N seconds (0 = no limit)")
    parser.add_argument("--refresh", action="store_true", help="remove existing skills before reinstalling")
    parser.add_argument("--state", default=os.path.expanduser("~/.agents/.skills-sh-top80-state.json"))
    parser.add_argument("--report", default=os.path.expanduser("~/.agents/.skills-sh-top80-report.json"))
    parser.add_argument("--no-link-codex", action="store_true")
    parser.add_argument("--no-link-claude", action="store_true")
    parser.add_argument("--resolve-missing", action="store_true", help="use GitHub API tree to find SKILL.md paths")
    args = parser.parse_args()

    if not os.path.isfile(args.installer):
        print(f"Installer not found: {args.installer}", file=sys.stderr)
        return 1

    os.makedirs(args.dest, exist_ok=True)

    state = load_state(args.state)
    skip_ids = set(state.get("skip_ids", []))
    path_cache = state.get("path_cache", {})
    tree_cache: Dict[str, List[str]] = {}

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    skills_json = fetch_skills_json(args.view, args.limit, timeout=args.timeout)
    skills = skills_json.get("skills", [])

    existing = set(os.listdir(args.dest)) if os.path.isdir(args.dest) else set()

    results = {"installed": [], "skipped": [], "failed": []}

    start = time.time()
    for skill in skills:
        if args.time_budget and (time.time() - start) > args.time_budget:
            break

        skill_id = skill.get("id")
        repo = skill.get("topSource")
        if not skill_id or not repo:
            continue

        dest_dir = os.path.join(args.dest, skill_id)
        if skill_id in existing or os.path.exists(dest_dir):
            if args.refresh:
                try:
                    if os.path.islink(dest_dir) or os.path.isfile(dest_dir):
                        os.unlink(dest_dir)
                    else:
                        shutil.rmtree(dest_dir)
                    existing.discard(skill_id)
                except OSError:
                    results["skipped"].append([skill_id, repo, "failed to remove existing"])
                    continue
            else:
                results["skipped"].append([skill_id, repo, "already exists"])
                continue
        if skill_id in skip_ids:
            results["skipped"].append([skill_id, repo, "path unresolved"])
            continue

        owner, repo_name = repo.split("/")
        cache_key = f"{repo}|{skill_id}"
        paths = []
        cached = path_cache.get(cache_key)
        if cached:
            paths.append(cached)
        paths.extend([p for p in candidate_paths(skill_id) if p not in paths])

        installed = False
        last_err = ""
        used_path = ""

        for path in paths:
            rc, out, err = install_skill(
                args.installer,
                repo,
                path,
                "main",
                args.dest,
                args.method,
                timeout=args.cmd_timeout,
            )
            if rc == 0:
                installed = True
                used_path = path
                break
            if "Destination already exists" in err:
                results["skipped"].append([skill_id, repo, "already exists"])
                installed = True
                used_path = path
                break
            if is_branch_error(err):
                rc, out, err = install_skill(
                    args.installer,
                    repo,
                    path,
                    "master",
                    args.dest,
                    args.method,
                    timeout=args.cmd_timeout,
                )
                if rc == 0:
                    installed = True
                    used_path = path
                    break
            if not is_path_error(err) and not is_branch_error(err):
                last_err = err or out
                break
            last_err = err or out

        if not installed and args.resolve_missing:
            try:
                resolved = discover_path_via_tree(
                    owner,
                    repo_name,
                    skill_id,
                    "main",
                    token,
                    timeout=args.timeout,
                    tree_cache=tree_cache,
                )
            except Exception:
                resolved = None
            if not resolved:
                try:
                    resolved = discover_path_via_tree(
                        owner,
                        repo_name,
                        skill_id,
                        "master",
                        token,
                        timeout=args.timeout,
                        tree_cache=tree_cache,
                    )
                except Exception:
                    resolved = None
            if resolved:
                rc, out, err = install_skill(
                    args.installer,
                    repo,
                    resolved,
                    "main",
                    args.dest,
                    args.method,
                    timeout=args.cmd_timeout,
                )
                if rc != 0 and is_branch_error(err):
                    rc, out, err = install_skill(
                        args.installer,
                        repo,
                        resolved,
                        "master",
                        args.dest,
                        args.method,
                        timeout=args.cmd_timeout,
                    )
                if rc == 0:
                    installed = True
                    used_path = resolved
                else:
                    last_err = err or out

        if installed:
            if used_path:
                path_cache[cache_key] = used_path
            try:
                if not args.no_link_codex:
                    ensure_symlink(dest_dir, os.path.expanduser("~/.codex/skills"))
                if not args.no_link_claude:
                    ensure_symlink(dest_dir, os.path.expanduser("~/.claude/skills"))
            except OSError:
                pass
            results["installed"].append([skill_id, repo])
            existing.add(skill_id)
        else:
            if is_path_error(last_err):
                skip_ids.add(skill_id)
            results["failed"].append([skill_id, repo, last_err])

        state["skip_ids"] = sorted(skip_ids)
        state["path_cache"] = path_cache
        save_state(args.state, state)

    with open(args.report, "w") as f:
        json.dump(results, f, indent=2)

    print(f"installed: {len(results['installed'])}")
    print(f"skipped: {len(results['skipped'])}")
    print(f"failed: {len(results['failed'])}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

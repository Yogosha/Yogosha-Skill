#!/usr/bin/env python3
"""
Yogosha API helper for the yogosha hunter skill.

Pure standard library. The session credentials are read from the environment,
NEVER from a file on disk:
    YOGOSHA_USER   - the platform username
    YOGOSHA_TOKEN  - the platform access token
They are set per-invocation by the skill from the in-context credentials and are
never printed, logged, or written anywhere.

Subcommands:
  check-attachments --report <id|link>
        Read-only. GET the report and report how many screenshots (markdown image
        insertions in the content) and whether a video attachment are present.
  create-draft --body-file <path.json> [--confirm]
        Create a draft report. DRY-RUN by default: prints the plan and posts nothing.
        Only with --confirm does it POST. The body file is the full POST payload
        (a JSON object with title, vulnerability, program, content), read as utf-8.

Base: https://api-cyber.yogosha.com  (HTTP Basic auth: base64(username:token))
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = "https://api-cyber.yogosha.com"
TIMEOUT = 30
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


def die(msg, code=2):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def creds():
    user = os.environ.get("YOGOSHA_USER")
    token = os.environ.get("YOGOSHA_TOKEN")
    if not user or not token:
        die("Set YOGOSHA_USER and YOGOSHA_TOKEN in the environment (run /yogosha:start first).")
    return user, token


def api(method, path, payload=None):
    user, token = creds()
    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        if e.code in (401, 403):
            die(f"Auth/permission error {e.code}. Check the username and access token.")
        return e.code, {"error": detail}
    except Exception as exc:
        die(f"Could not reach the Yogosha API: {exc}")


def report_id(s):
    s = s.strip()
    m = re.search(r"/reports/([A-Za-z0-9]+)", s)
    if m:
        return m.group(1)
    return s


IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def cmd_check_attachments(args):
    rid = report_id(args.report)
    status, rep = api("GET", f"/api/reports/{rid}?embed=content")
    if status != 200:
        die(f"Could not read report {rid} (HTTP {status}). {rep.get('error','')}")
    content = rep.get("content") or {}
    fields = ["abstract", "proofOfConcept", "remediation"]
    shots = sum(len(IMG_RE.findall(content.get(f) or "")) for f in fields)
    try:
        videos = int(content.get("videosCount") or 0)
    except (TypeError, ValueError):
        videos = 0
    print(json.dumps({
        "ok": True,
        "reportId": rid,
        "screenshots": shots,
        "videos": videos,
        "video": videos > 0,
    }, ensure_ascii=False))


def cmd_create_draft(args):
    try:
        body = json.loads(open(args.body_file, encoding="utf-8").read())
    except Exception as exc:
        die(f"Could not read body file {args.body_file}: {exc}")
    for k in ("title", "vulnerability", "program"):
        if not body.get(k):
            die(f"Draft body is missing the required field: {k}")
    plan = {
        "endpoint": "POST /api/reports",
        "title": body.get("title"),
        "vulnerability": body.get("vulnerability"),
        "program": body.get("program"),
        "contentKeys": sorted((body.get("content") or {}).keys()),
    }
    if not args.confirm:
        print(json.dumps({"ok": True, "dryRun": True, "plan": plan}, ensure_ascii=False))
        return
    status, rep = api("POST", "/api/reports", body)
    if status not in (200, 201):
        die(f"Create failed (HTTP {status}). {rep.get('error','')}")
    rid = rep.get("id") or rep.get("reference")
    print(json.dumps({
        "ok": True,
        "created": True,
        "reportId": rid,
        "reference": rep.get("reference"),
    }, ensure_ascii=False))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Yogosha hunter API helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("check-attachments", help="count screenshots and video on a draft")
    p1.add_argument("--report", required=True, help="report id or link")

    p2 = sub.add_parser("create-draft", help="create a draft report (dry-run unless --confirm)")
    p2.add_argument("--body-file", required=True, help="JSON file with the full POST body")
    p2.add_argument("--confirm", action="store_true", help="actually POST the draft")

    args = ap.parse_args()
    {"check-attachments": cmd_check_attachments, "create-draft": cmd_create_draft}[args.cmd](args)


if __name__ == "__main__":
    main()

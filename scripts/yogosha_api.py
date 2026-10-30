#!/usr/bin/env python3
"""
Yogosha API helper for the yogosha hunter skill.

Pure standard library. The session credentials are read from the environment,
NEVER from a file on disk:
    YOGOSHA_USER   - the platform username
    YOGOSHA_TOKEN  - the platform access token
They are set per-invocation by the skill from the in-context credentials and are
never printed, logged, or written anywhere.

The API base defaults to https://api-cyber.yogosha.com and can be overridden with
YOGOSHA_API_BASE for a regional instance (for example https://api-uae.yogosha.com).

Subcommands:
  find-program --name <text>
        Read-only. Search the programs the hunter can see by partial, case-insensitive
        name and print each match with its id, state, scope list and out-of-scope text,
        so the scope check and the create-draft program id come from the platform.
  check-attachments --report <id|link>
        Read-only. GET the report and report how many screenshots (markdown image
        insertions in the content) and whether a video attachment are present.
  create-draft --body-file <path.json> [--confirm]
        Create a draft report. DRY-RUN by default: prints the plan and posts nothing.
        Only with --confirm does it POST. The body file is the full POST payload
        (a JSON object with title, vulnerability, program, content), read as utf-8.
        content.cvssResearcher takes only {"vector": "CVSS:4.0/..."}; the platform
        computes the score and severity.
  comment --report <id|link> (--body <text> | --body-file <path>) [--visibility public] [--parent <id>] [--confirm]
        Post a comment on a report's thread (for example to answer a triager on an
        already-submitted report). DRY-RUN by default. --parent replies to a comment.
        The API only exposes the hunter's own reports, so this is limited to them.
  submit-report --report <id|link> --vulnerability <CODE> [--confirm]
        Submit a draft report (PUT .../submit). DRY-RUN by default: prints the plan.
        Only with --confirm does it submit. Submit re-validates the whole report, so
        the body is rebuilt from the report's CURRENT content (preserving screenshots
        added in the UI) plus the vulnerability class code (the read returns only a
        slug, so pass the same code used at create). Submitting is the hunter's decision.

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

BASE = os.environ.get("YOGOSHA_API_BASE", "https://api-cyber.yogosha.com").rstrip("/")
# The Basic credential is only ever sent to an official Yogosha API host over TLS.
# YOGOSHA_API_BASE is security-relevant: an unvalidated or http:// base would ship
# the token offsite, or send it in cleartext. Reject anything that is not an
# https://api-<instance>.yogosha.com host before any request carries the credential.
_BASE_RE = re.compile(r"^https://api-[a-z0-9-]+\.yogosha\.com$")
TIMEOUT = 30
# A browser User-Agent is required: the api-*.yogosha.com edge (Cloudflare) rejects
# the default python-urllib User-Agent with "error 1010". This is a compatibility
# workaround, not an attempt to disguise the client.
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
    if not _BASE_RE.match(BASE):
        die(f"Refusing to use YOGOSHA_API_BASE={BASE!r}: it must be an official Yogosha "
            f"API host over HTTPS (https://api-<instance>.yogosha.com).")
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
    if re.fullmatch(r"[A-Za-z0-9]+", s):
        return s
    die(f"Not a valid report id or link: {s!r}. Expected an alphanumeric id or a "
        f"/reports/<id> link.")


IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def cmd_find_program(args):
    needle = args.name.strip().lower()
    if not needle:
        die("Give part of the program name with --name.")
    matches, page = [], 1
    while True:
        status, res = api("GET", f"/api/programs?limit=100&page={page}")
        if status != 200:
            die(f"Could not list programs (HTTP {status}). {res.get('error','')}")
        items = res.get("data") or []
        for prog in items:
            if needle in str(prog.get("name") or "").lower():
                matches.append(prog)
        pages = int((res.get("pagination") or {}).get("totalPages") or 1)
        if not items or page >= pages:
            break
        page += 1
    out = []
    for prog in matches:
        status, full = api("GET", f"/api/programs/{prog['id']}?embed=content")
        content = (full.get("content") or {}) if status == 200 else {}
        out.append({
            "id": prog.get("id"),
            "name": prog.get("name"),
            "type": prog.get("type"),
            "state": prog.get("state"),
            "vpnRequired": prog.get("vpnRequired"),
            "scope": full.get("scope") if status == 200 else None,
            "outOfScopes": full.get("outOfScopes") if status == 200 else None,
            "outOfScopeText": (content.get("outOfScope") or "")[:2000],
        })
    print(json.dumps({"ok": True, "matches": out, "count": len(out)}, ensure_ascii=False))


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


def cmd_comment(args):
    rid = report_id(args.report)
    if args.body_file:
        try:
            body_text = open(args.body_file, encoding="utf-8").read().strip()
        except Exception as exc:
            die(f"Could not read comment body file {args.body_file}: {exc}")
    else:
        body_text = (args.body or "").strip()
    if not body_text:
        die("The comment body is empty. Pass --body or --body-file.")
    status, rep = api("GET", f"/api/reports/{rid}?embed=content")
    if status != 200:
        die(f"Could not read report {rid} (HTTP {status}). {rep.get('error','')}")
    tid = rep.get("threadId")
    if not tid:
        die(f"Report {rid} has no thread to comment on (is it submitted?).")
    payload = {"body": body_text, "visibility": args.visibility}
    if args.parent:
        payload["parentId"] = args.parent
    plan = {
        "endpoint": f"POST /api/threads/{tid}/comments",
        "reportId": rid,
        "threadId": tid,
        "visibility": args.visibility,
        "reply": bool(args.parent),
        "bodyPreview": body_text[:160],
    }
    if not args.confirm:
        print(json.dumps({"ok": True, "dryRun": True, "plan": plan}, ensure_ascii=False))
        return
    status, res = api("POST", f"/api/threads/{tid}/comments", payload)
    if status not in (200, 201):
        die(f"Comment failed (HTTP {status}). {res.get('error','')}")
    print(json.dumps({
        "ok": True,
        "posted": True,
        "reportId": rid,
        "threadId": tid,
        "commentId": res.get("id"),
    }, ensure_ascii=False))


def cmd_submit_report(args):
    rid = report_id(args.report)
    status, rep = api("GET", f"/api/reports/{rid}?embed=content,program")
    if status != 200:
        die(f"Could not read report {rid} (HTTP {status}). {rep.get('error','')}")
    content = rep.get("content") or {}
    vector = (content.get("cvssResearcher") or {}).get("vector")
    program = (rep.get("program") or {}).get("id")
    # Submit re-validates the whole report. Rebuild the body from the CURRENT content
    # (so screenshots added in the UI are preserved) plus the vulnerability class code,
    # which the read returns only as a slug, so the caller passes it.
    body = {
        "title": rep.get("title"),
        "vulnerability": args.vulnerability,
        "program": program,
        "content": {
            "abstract": content.get("abstract"),
            "proofOfConcept": content.get("proofOfConcept"),
            "remediation": content.get("remediation"),
            "scopeUrl": content.get("scopeUrl"),
            "cvssResearcher": {"vector": vector} if vector else None,
        },
    }
    plan = {
        "endpoint": f"PUT /api/reports/{rid}/submit",
        "reportId": rid,
        "title": rep.get("title"),
        "vulnerability": args.vulnerability,
        "currentStatus": rep.get("status"),
        "cvssVector": vector,
    }
    if not args.confirm:
        print(json.dumps({"ok": True, "dryRun": True, "plan": plan}, ensure_ascii=False))
        return
    status, res = api("PUT", f"/api/reports/{rid}/submit", body)
    if status not in (200, 201, 204):
        die(f"Submit failed (HTTP {status}). {res.get('error','')}")
    print(json.dumps({
        "ok": True,
        "submitted": True,
        "reportId": rid,
        "status": (res or {}).get("status"),
    }, ensure_ascii=False))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Yogosha hunter API helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p0 = sub.add_parser("find-program", help="search programs by name; prints id, scope, out-of-scope")
    p0.add_argument("--name", required=True, help="part of the program name")

    p1 = sub.add_parser("check-attachments", help="count screenshots and video on a draft")
    p1.add_argument("--report", required=True, help="report id or link")

    p2 = sub.add_parser("create-draft", help="create a draft report (dry-run unless --confirm)")
    p2.add_argument("--body-file", required=True, help="JSON file with the full POST body")
    p2.add_argument("--confirm", action="store_true", help="actually POST the draft")

    p3 = sub.add_parser("comment", help="post a comment on a report thread (dry-run unless --confirm)")
    p3.add_argument("--report", required=True, help="report id or link")
    p3.add_argument("--body", help="comment text")
    p3.add_argument("--body-file", help="file with the comment text (preferred over --body)")
    p3.add_argument("--visibility", default="public", help="comment visibility (default: public)")
    p3.add_argument("--parent", help="parent comment id, to reply in a thread")
    p3.add_argument("--confirm", action="store_true", help="actually POST the comment")

    p4 = sub.add_parser("submit-report", help="submit a draft report (dry-run unless --confirm)")
    p4.add_argument("--report", required=True, help="report id or link")
    p4.add_argument("--vulnerability", required=True, help="vulnerability class code used at create (e.g. API1)")
    p4.add_argument("--confirm", action="store_true", help="actually submit the report")

    args = ap.parse_args()
    {
        "find-program": cmd_find_program,
        "check-attachments": cmd_check_attachments,
        "create-draft": cmd_create_draft,
        "comment": cmd_comment,
        "submit-report": cmd_submit_report,
    }[args.cmd](args)


if __name__ == "__main__":
    main()

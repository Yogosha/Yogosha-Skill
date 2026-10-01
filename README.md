# yogosha-skill - report-quality rules for Yogosha hunters, on any agent

Rules of engagement and report-quality guidance that help a hunter's AI agent submit bug bounty reports which survive triage: capture the one proof that matters, force rigorous controls, push back hard on an inflated CVSS score, keep testing in scope and non-destructive, and follow a clean report structure. Built from the triager's own checklist, the same things a report is graded on.

## This is an advisory aid, not a security control

These rules make a cooperating agent more likely to stay in scope, test non-destructively, and score honestly. They do not sandbox anything and cannot stop a determined or malicious operator, and they only take effect in an agent that loads them. Real prevention is infrastructure: a scoped egress proxy or VPN that only reaches in-scope hosts, rate limiting, and test-only data. Use these rules as the quality layer on top of that.

## What it enforces (behaviourally)

- **Load-bearing proof.** The single decisive step that proves the finding must be shown, not asserted.
- **Controls.** The negative tests (junk id to 404, foreign id to 403, corrupted token to error, unchanged write to baseline) that turn a positive result into proof.
- **Honest CVSS 4.0.** Interrogates the vector metric by metric, drops any High or Critical value not backed by evidence, and lands a defensible score.
- **Technical sanity.** Catches the classic false positives that get reports rejected.
- **Scope and conduct.** Checks the target against the program scope and out-of-scope before testing and before submitting.
- **Report structure.** One clean skeleton, proof-first, with screenshot markers.

## One source, many agents

`RULES.md` is the canonical rules of engagement. `report-structure.md` is the shared report skeleton and pre-submit checklist. The files under `adapters/` embed that same content in each tool's native format, so the methodology never forks.

| Agent | Use this | Where it goes |
| --- | --- | --- |
| Claude Code | the plugin at the repo root | `/plugin marketplace add https://gitlab.yogosha.com/H4MA/yogosha-skill.git` then `/plugin install yogosha@yogosha-skill` |
| Claude Code (no plugin) | `adapters/claude-md/CLAUDE.md` | repo root as `CLAUDE.md` |
| Codex / OpenAI CLI | `adapters/codex/AGENTS.md` | repo root as `AGENTS.md` (read automatically) |
| Cursor | `adapters/cursor/.cursor/rules/report-quality.mdc` | `.cursor/rules/` in your project |
| Windsurf | `adapters/windsurf/.windsurfrules` | workspace root |
| Continue | `adapters/continue/rules.md` | a rules block in your Continue config |
| Raw API agent | `adapters/raw-api/system-prompt.txt` | prepend as the system message |

Each adapter file is self-contained: copy the one file for your agent and you have the full rules and report structure.

## Claude Code plugin (the full flow)

Beyond the rules, the Claude Code plugin adds commands that create the draft on the platform and verify its attachments before you submit.

- `/yogosha:start <username> <access_token>` - authenticate. The token stays in conversation context only and is never written to disk.
- `/yogosha:report <finding notes>` - understand, scope-check, run the PoC and controls non-destructively, run the CVSS reality-check, draft the report, and (when authenticated) create the draft on the platform.
- `/yogosha:report <report-link>` - after you attach screenshots, re-check that the screenshots or video are present and give the ready-to-submit verdict.
- `/yogosha:clean` - wipe local drafts and session state at the end.

The `report-quality` skill also activates on its own whenever you are writing a report, so its rules apply even outside the commands.

## Attachment check

`scripts/yogosha_api.py check-attachments --report <id|link>` reads the draft and reports how many screenshots (markdown image insertions in the content) and whether a video are present. It is a presence and count check: it confirms the images and video exist, not what they depict. Credentials are read from the environment only, never a file.

## Requirements

- Python 3 (standard library only).
- The `code` CLI is used to open the local draft, if available.

## Security

- Your Yogosha access token lives only in the conversation context, passed to the helper through an environment variable per call, never a config file, never written to disk.
- The rules test non-destructively and only in scope. They will not read real customers' data or perform destructive actions to show impact.
- Run `/yogosha:clean` (or delete local drafts) when you finish.

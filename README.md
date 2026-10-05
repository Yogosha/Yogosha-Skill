# yogosha-skill - report-quality rules for Yogosha hunters, on any agent

Rules of engagement and report-quality guidance that help a hunter's AI agent submit bug bounty reports which survive triage: capture the one proof that matters, force rigorous controls, push back hard on an inflated CVSS score, keep testing in scope and non-destructive, and follow a clean report structure. Built from the triager's own checklist, the same things a report is graded on.

This README is the overview. The full reference (layout, every command step by step, both transports, security model, maintenance, troubleshooting) is in [DOCUMENTATION.md](DOCUMENTATION.md).

## This is an advisory aid, not a security control

These rules make a cooperating agent more likely to stay in scope, test non-destructively, and score honestly. They do not sandbox anything and cannot stop a determined or malicious operator, and they only take effect in an agent that loads them. Real prevention is infrastructure: a scoped egress proxy or VPN that only reaches in-scope hosts, rate limiting, and test-only data. Use these rules as the quality layer on top of that.

## What it enforces (behaviourally)

- **Load-bearing proof.** The single decisive step that proves the finding must be shown, not asserted.
- **Controls.** The negative tests (junk id to 404, foreign id to 403, corrupted token to error, unchanged write to baseline) that turn a positive result into proof.
- **Honest CVSS 4.0.** Interrogates the vector metric by metric, drops any High or Critical value not backed by evidence, and lands a defensible score.
- **Technical sanity.** Catches the classic false positives that get reports rejected.
- **Scope and conduct.** Checks the target against the program scope and out-of-scope before testing and before submitting.
- **Report structure.** One clean skeleton, proof-first, with screenshot markers.
- **Platform discipline.** Through the official Yogosha MCP or the API, the agent creates and reads its own drafts only; it never submits, edits other reports, or deletes anything.

## One source, many agents

`RULES.md` is the canonical rules of engagement, including the report skeleton and pre-submit checklist. The files under `adapters/` are generated from it by `scripts/build_adapters.py`, each with a header in that tool's native format, so the methodology never forks. CI fails if an adapter drifts.

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

- `/yogosha:start mcp` or `/yogosha:start <username> <access_token>` - start a session and pick how the plugin reaches the platform (see below).
- `/yogosha:report <finding notes>` - understand, scope-check, run the PoC and controls non-destructively, run the CVSS reality-check, draft the report, and (when authenticated) create the draft on the platform.
- `/yogosha:report <report-link>` - after you attach screenshots, re-check that the screenshots or video are present, give the ready-to-submit verdict, and submit on your explicit go-ahead (API transport; the MCP has no submit tool so submit is a UI action).
- `/yogosha:comment <report> <what to say>` - draft a reply on one of your reports (for example to answer a triager) and post it after you confirm the wording.
- `/yogosha:clean` - wipe local drafts and session state at the end.

The `report-quality` skill also activates on its own whenever you are writing a report, so its rules apply even outside the commands.

## Two ways to reach the platform

The hunter chooses at `/yogosha:start`. With no argument the plugin auto-detects: if the Yogosha MCP tools are present it uses them, otherwise it asks for API credentials.

| | Official Yogosha MCP | API helper script |
| --- | --- | --- |
| Start | `/yogosha:start mcp` | `/yogosha:start <username> <access_token>` |
| Setup | one-time `claude mcp add` (below) | none, Python 3 only |
| Where the token lives | in the MCP server config, fed from an env var; never in the conversation | in conversation context, passed to the script per call; never on disk |
| Program and scope lookup | reads the program scope and out-of-scope through the MCP, resolves the program id and vulnerability class for you | you confirm the program id and class code by hand |
| Create draft, check attachments | MCP tools | `scripts/yogosha_api.py` |
| Works outside Claude Code | yes, any MCP client (Cursor, Codex, ...) | yes, anywhere Python runs |

Whichever transport is used, the plugin acts only on your own reports, and every write (create a draft, comment, submit) waits for your explicit confirmation. Submitting is available over the API transport; the MCP has no submit tool, so there you submit in the Yogosha UI. It never fabricates evidence or comment text.

### Setting up the official Yogosha MCP

The MCP server is the platform's own: every documented API endpoint is exposed as a tool, with the same Basic authentication as the API (docs: https://developers.yogosha.com/#tag/Yogosha-MCP).

1. Create an API key under Settings > API Keys with the scopes you need (programs read, reports read and create).
2. Put the Basic credential in your shell environment, so it never lands in a config file in a repo:
   ```
   export YOGOSHA_BASIC=$(printf '%s:%s' '<username>' '<access_token>' | base64)
   ```
3. Register the server once:
   ```
   claude mcp add --transport http yogosha https://api-cyber.yogosha.com/mcp --header "Authorization: Basic ${YOGOSHA_BASIC}"
   ```
4. Restart Claude Code and run `/yogosha:start mcp`.

On a shared machine, `claude mcp remove yogosha` and unset `YOGOSHA_BASIC` when you are done.

## Attachment check

Before you submit, the plugin reads the draft and reports how many screenshots (markdown image insertions in the content) and whether a video are present. Through the MCP it reads the report with the get-report tool; through the API it runs `scripts/yogosha_api.py check-attachments --report <id|link>`. It is a presence and count check: it confirms the images and video exist, not what they depict. In API mode credentials are read from the environment only, never a file.

## Regional instances

The default instance is `https://api-cyber.yogosha.com`. On a regional instance (for example `https://api-uae.yogosha.com`):

- MCP: register the server with that instance's `/mcp` URL instead.
- API: set `YOGOSHA_API_BASE` to the instance before running the commands.

Authenticate with a token issued for that instance; the access token is instance-specific.

## Requirements

- Claude Code with the plugin installed. For the MCP transport, the Yogosha MCP server registered as above.
- Python 3 (standard library only) for the API transport.
- The `code` CLI is used to open the local draft, if available.

## Security

- Your Yogosha access token is never written to disk by this plugin. In MCP mode it lives in the MCP server config, fed from an environment variable, and never enters the conversation. In API mode it lives only in the conversation context and is passed to the helper through an environment variable per call.
- The plugin creates and reads its own drafts only. Submit, edit of other reports, and every destructive platform tool are off limits to the agent.
- The rules test non-destructively and only in scope. They will not read real customers' data or perform destructive actions to show impact.
- Run `/yogosha:clean` (or delete local drafts) when you finish.

## Maintaining

Edit `RULES.md`, then run `python scripts/build_adapters.py` to regenerate the adapters. CI runs the same script with `--check` plus a smoke test of the API helper and GitLab secret detection.

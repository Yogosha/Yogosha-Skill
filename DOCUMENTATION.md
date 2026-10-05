# yogosha-skill documentation

Everything in one place: what the project is, how to install it on each agent, the full Claude Code workflow, the two platform transports, the files, and how to maintain it. The short version is in `README.md`.

## 1. What this is

A set of rules of engagement and report-quality guidance for an AI coding agent that assists a bug bounty hunter on Yogosha, plus a Claude Code plugin that drives the whole flow: prove the finding, score it honestly, draft the report, create the draft on the platform, and verify the attachments before the hunter submits.

The rules are built from the triager's own checklist. A report is graded on five things: the decisive proof is shown, controls rule out noise, the CVSS score matches what was demonstrated, the target is in scope and the testing was non-destructive, and the write-up is clear. The skill enforces each one.

It is an advisory aid, not a security control. It makes a cooperating agent more likely to stay in scope, test non-destructively, and score honestly. It does not sandbox anything and cannot stop a malicious operator. Real prevention is infrastructure: a scoped egress proxy or VPN that only reaches in-scope hosts, rate limiting, and test-only data.

## 2. Project layout

```
.claude-plugin/
  plugin.json            plugin manifest (name "yogosha", version, metadata)
  marketplace.json       marketplace manifest so the repo can be added as a plugin source
commands/
  start.md               /yogosha:start   - pick the transport and verify access
  report.md              /yogosha:report  - build, score, draft, create, verify, submit
  comment.md             /yogosha:comment - draft and post a comment on your report
  clean.md               /yogosha:clean   - wipe drafts and session state
skills/report-quality/
  SKILL.md               the report-quality skill (auto-activates when writing a report)
templates/
  report-skeleton.md     fill-in skeleton the plugin drafts from
scripts/
  yogosha_api.py         API helper (create draft, check attachments), stdlib only
  build_adapters.py      regenerates adapters/ from RULES.md
RULES.md                 canonical rules of engagement + report skeleton + checklist
adapters/                the same rules in each tool's native format (generated)
  claude-md/CLAUDE.md
  codex/AGENTS.md
  continue/rules.md
  cursor/.cursor/rules/report-quality.mdc
  windsurf/.windsurfrules
  raw-api/system-prompt.txt
.gitlab-ci.yml           CI: adapter sync check, script smoke test, secret detection
LICENSE                  MIT
```

## 3. Installation

### Claude Code plugin (full flow)

```
/plugin marketplace add https://gitlab.yogosha.com/H4MA/yogosha-skill.git
/plugin install yogosha@yogosha-skill
```

This gives you the three `/yogosha:*` commands and the `report-quality` skill.

### Rules only, on any agent

Copy the one file for your tool. Each adapter is self-contained.

| Agent | File | Where it goes |
| --- | --- | --- |
| Claude Code (no plugin) | `adapters/claude-md/CLAUDE.md` | repo root as `CLAUDE.md` |
| Codex / OpenAI CLI | `adapters/codex/AGENTS.md` | repo root as `AGENTS.md` |
| Cursor | `adapters/cursor/.cursor/rules/report-quality.mdc` | `.cursor/rules/` |
| Windsurf | `adapters/windsurf/.windsurfrules` | workspace root |
| Continue | `adapters/continue/rules.md` | a rules block in your Continue config |
| Raw API agent | `adapters/raw-api/system-prompt.txt` | the system message |

Agents other than Claude Code can also use the official Yogosha MCP directly (section 5); the rules tell them how to behave with it.

## 4. The Claude Code workflow

### `/yogosha:start`

Starts a session and chooses how the plugin reaches the platform.

- `/yogosha:start mcp` uses the official Yogosha MCP server. Requires the server to be registered (section 5). Verifies by listing programs.
- `/yogosha:start <username> <access_token>` uses the bundled API helper. Verifies with `GET /api/programs?limit=1`.
- `/yogosha:start` with no argument auto-detects: MCP tools present means MCP, otherwise it prints the usage.

On success it writes a non-secret marker to the session scratchpad as `.session.json`:

```json
{"authenticated": true, "transport": "mcp" | "api", "username": "...", "apiBase": "..."}
```

`username` and `apiBase` are present only when known. The token is never in the marker.

### `/yogosha:report <finding notes>` (Mode A)

1. Understand: restate the vulnerability, exact target, and preconditions.
2. Scope check, first: confirm the target and action are in scope and not excluded. In MCP mode the program scope is read from the platform. Out of scope means stop before any testing.
3. Plan the PoC: the one load-bearing step and the controls (junk id -> 404, foreign id -> 403, corrupted token -> error, unchanged write -> baseline).
4. Run it, non-destructively, on own or test accounts. Destructive proofs are marked NEEDS MANUAL VERIFICATION instead of faked.
5. CVSS 4.0 reality-check: the hunter's proposed vector is interrogated metric by metric; anything High or Critical without captured evidence is dropped. The realistic vector goes in the report. This gate cannot be skipped.
6. Draft from `templates/report-skeleton.md`, with `[[screenshot: ...]]` markers where images belong. Saved to `report/<slug>.md` and opened in VS Code if the `code` CLI exists.
7. Self-triage: an adversarial review with a READY or NOT READY verdict.
8. Create the draft, only if READY and authenticated. The body is shown as a dry run and nothing is sent until the hunter confirms. MCP: the create-report tool. API: `yogosha_api.py create-draft` dry run, then `--confirm`.
9. Hand off: attach screenshots on the platform, then run Mode B.

### `/yogosha:report <report-link or id>` (Mode B)

Reads the draft and counts markdown image insertions in the abstract, proof of concept, and remediation fields, plus the video count. If the screenshots marked in Mode A are present (and a video where needed) it says the report is ready to submit. If anything is missing it names what, and stops. It is a presence check: it confirms attachments exist, not what they depict.

Submitting is confirm-gated and only on the hunter's explicit request, and only once the report is READY. Over the API transport the plugin submits via `submit-report` (which re-validates the whole report and rebuilds the body from the current content, so screenshots are preserved). The Yogosha MCP has no submit tool, so over MCP the hunter submits in the UI. The agent never submits on its own.

### `/yogosha:comment <report link|id> <what to say>`

Drafts a comment on one of the hunter's own reports (for example to answer a triager on an already-submitted report), shows the exact wording, and posts it only after the hunter confirms. Over MCP it uses `create_a_thread_comment` (thread resolved from `get_a_report`); over the API it uses the `comment` subcommand. Access is limited by the platform to the hunter's own reports. The reply must be factual; it never invents evidence. A comment does not submit the report.

### `/yogosha:clean`

Deletes `report/`, the session scratchpad (marker and any body files), pulled test data in temp and output dirs, and testing artefacts (`*.json`, `*.zip`, `*.pdf`, `*.eml`, `*.har`) in the working directory. Then lists the directory and confirms nothing with target data, PII, or credentials remains. In MCP mode it reminds the hunter to remove the server and unset the env var on shared machines.

### The `report-quality` skill

Loaded automatically whenever a report is being written, reviewed, or scored, even outside the commands. Its ten sections mirror `RULES.md`: load-bearing proof, controls, non-destructive discipline, the CVSS reality-check, technical sanity (common false positives), scope and conduct, impact honesty, consolidation, report craft, attachments.

## 5. Platform transports

### Official Yogosha MCP

The platform's own MCP server at `https://api-cyber.yogosha.com/mcp` (streamable HTTP, protocol versions 2025-03-26 and 2025-06-18). Every documented API endpoint is exposed as a tool. Authentication is the same HTTP Basic credential as the API. Docs: https://developers.yogosha.com/#tag/Yogosha-MCP.

Setup, once:

1. Create an API key under Settings > API Keys with the scopes you need (programs read, reports read and create).
2. Put the Basic credential in your shell environment:
   ```
   export YOGOSHA_BASIC=$(printf '%s:%s' '<username>' '<access_token>' | base64)
   ```
3. Register the server:
   ```
   claude mcp add --transport http yogosha https://api-cyber.yogosha.com/mcp --header "Authorization: Basic ${YOGOSHA_BASIC}"
   ```
4. Restart Claude Code, then `/yogosha:start mcp`.

The token lives in the MCP server config and never enters the conversation. Yogosha does not publish the MCP tool names, so the commands pick tools by purpose (list programs, get program, create report, get report).

### API helper script

`scripts/yogosha_api.py`, standard library only. Credentials come from the environment per call, set by the plugin from the in-context credentials, never from a file.

Export the credentials once in your shell, then call the script plainly so the token never appears in a command (the harness records commands to the session transcript):

```
export YOGOSHA_USER=<username> YOGOSHA_TOKEN=<token>
python scripts/yogosha_api.py find-program --name "<part of a program name>"
python scripts/yogosha_api.py check-attachments --report <id|link>
python scripts/yogosha_api.py create-draft --body-file body.json                               # dry run
python scripts/yogosha_api.py create-draft --body-file body.json --confirm                     # POST
python scripts/yogosha_api.py comment --report <id|link> --body-file reply.txt                  # dry run
python scripts/yogosha_api.py comment --report <id|link> --body-file reply.txt --confirm        # POST
python scripts/yogosha_api.py submit-report --report <id|link> --vulnerability API1             # dry run
python scripts/yogosha_api.py submit-report --report <id|link> --vulnerability API1 --confirm   # submit
```

Output is one JSON object per call. Every write subcommand (`create-draft`, `comment`, `submit-report`) is dry-run by default and only acts with `--confirm`. The create body file is the full POST payload: `title`, `vulnerability` (class code), `program` (id), and `content` with `abstract`, `proofOfConcept`, `remediation`, `scopeUrl`, and `cvssResearcher` (`{"vector": "CVSS:4.0/..."}`; the platform computes the score and severity). `submit-report` re-validates the whole report, so it rebuilds the body from the report's current content and needs the same vulnerability class code used at create. `comment` resolves the report's thread and posts with `visibility` `public`; `--parent <commentId>` replies to a specific message.

### Choosing

| | MCP | API helper |
| --- | --- | --- |
| Setup | one `claude mcp add` | none |
| Token | in MCP config, fed from an env var | in conversation context, per call |
| Program lookup | reads scope and resolves ids from the platform | hunter confirms ids by hand |
| Other agents | any MCP client | anywhere Python runs |

### Regional instances

Default instance: `https://api-cyber.yogosha.com`. For a regional instance such as `https://api-uae.yogosha.com`:

- MCP: register the server with that instance's `/mcp` URL.
- API: set `YOGOSHA_API_BASE` to the instance base before the commands run; `/yogosha:start` records it in the session marker.

Tokens are instance-specific.

## 6. Platform discipline (both transports)

The agent acts only on the hunter's own reports, and every outward action is confirm-gated. It may create and read drafts, comment on the hunter's own report (after showing the draft reply), and submit it (only when asked, API transport). Create, submit, and comment are single committed actions: each is called once, and on error the agent reports and stops rather than retrying, so a flaky transport cannot leave probe drafts or duplicate comments. It never fabricates evidence or comment text, and submitting stays the hunter's decision. Triage and organization actions (accepting a report, changing its review status, deleting) are reserved by the platform for those accounts and sit outside the hunter flow. This rule is in `RULES.md`, the skill, and every adapter.

## 7. Security model

- The access token is never written to disk by this project. MCP mode: in the MCP server config, fed from an env var, never in the conversation. API mode: supplied through environment variables; the recommended setup is to export `YOGOSHA_USER` and `YOGOSHA_TOKEN` before launching so the token never enters the conversation or any command. The helper never reads credentials from a file.
- Caution (API mode): anything typed into a shell command, including an inline `VAR=secret` or `export`, is recorded by the harness into the session transcript on disk. The commands therefore never put the token in a command; the script inherits it from the environment. If the token was passed to `/yogosha:start` as an argument, `/yogosha:clean` wipes the transcript that captured it.
- The session marker holds no secrets.
- The only files written are the local draft under `report/` and, in API mode, the JSON body or comment text in the session scratchpad. `/yogosha:clean` removes them.
- Testing is in scope and non-destructive by rule. No real customer data is read, no destructive action is taken to show impact.
- CI runs GitLab secret detection on every push.

## 8. Maintenance

- Edit the rules in `RULES.md` only. Then run `python scripts/build_adapters.py` to regenerate the six adapters. `python scripts/build_adapters.py --check` is what CI runs; it fails when an adapter drifted.
- Keep `skills/report-quality/SKILL.md` aligned with `RULES.md` by hand; it is the same content phrased for the skill loader, with the Yogosha-specific attachment notes.
- `templates/report-skeleton.md` is the fill-in version of the skeleton in `RULES.md`. Change both together.
- Bump `version` in `.claude-plugin/plugin.json` when commands or the skill change behaviour.
- All text files are LF (`.gitattributes`). No em dashes in any user-facing output; arrows are written as `->`.

## 9. Troubleshooting

- `/yogosha:start mcp` says the MCP tools are missing: the server is not registered or Claude Code was not restarted after `claude mcp add`. Check with `claude mcp list`.
- 401 or 403 at start: wrong username or token, token for another instance, or missing API key scopes.
- `check-attachments` reports zero screenshots after you attached them: images must be inserted into the report content (markdown image insertions), not only uploaded. Video is counted separately.
- `create-draft` fails with a missing field: `title`, `vulnerability`, and `program` are required; the plugin confirms both ids with you before the call.
- `create-draft` returns 400 "title: Some characters are not allowed": the title cannot contain certain characters (for example braces, slashes, or an apostrophe). Rephrase the title in plain words and create again; this is a deterministic validation bounce that creates nothing, so a single retry with a clean title is safe.
- `comment` returns "Access Forbidden" on a report that has a thread: the report is still a draft. A thread accepts comments only once the report is submitted and under review, so submit first, then comment. The plugin checks the status before posting and does not retry.
- Submitting over MCP: the Yogosha MCP has no submit tool, so submit in the UI or use an API-transport session (`/yogosha:start api`). This is expected, not a failure.
- The draft did not open in VS Code: the `code` CLI is not on PATH. The file is still at `report/<slug>.md`.

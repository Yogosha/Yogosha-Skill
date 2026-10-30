# yogosha-skill

Guardrails and report-quality rules for AI agents used in Yogosha bug bounty work. They keep an agent in scope and non-destructive, make it score CVSS honestly, and help it write reports that pass triage. For Claude Code there is also a plugin that drafts the report, creates it on the platform, checks its attachments, and submits or comments on your explicit go-ahead.

It shapes a cooperating agent's behavior. It is not a sandbox and will not stop a malicious one. Real isolation is infrastructure: a scoped egress proxy or VPN, rate limiting, and test-only data. These rules are the quality layer on top.

## Install (Claude Code plugin)

```
/plugin marketplace add https://github.com/Yogosha/Yogosha-Skill.git
/plugin install yogosha@yogosha-skill
```

That gives you the commands below and a `report-quality` skill that loads on its own whenever you write a report. To also have the plugin create drafts, comment, and submit on the platform, set up one of the two transports under [Reaching the platform](#reaching-the-platform).

## Commands

- `/yogosha:start` - begin a session and pick the transport: `mcp`, `api` (reads `YOGOSHA_USER` and `YOGOSHA_TOKEN` from the environment), or `<username> <token>`.
- `/yogosha:report <notes>` - scope-check, run the proof and controls non-destructively, interrogate the CVSS score, draft the report, and create the draft on the platform after you confirm.
- `/yogosha:report <report link>` - re-check attachments on a draft, give the ready verdict, and submit on your explicit go-ahead (API transport; the MCP has no submit tool, so there you submit in the UI).
- `/yogosha:comment <report> <what to say>` - draft a reply on one of your reports, for example to answer a triager, and post it after you confirm the wording.
- `/yogosha:clean` - wipe the session's local drafts and state.

## What the rules enforce

- Proof, not assertion. The one decisive step that proves the finding is shown, not described.
- Controls beside it. The negative tests that rule out noise: junk id -> 404, foreign id -> 403, corrupted token -> error, unchanged write -> baseline.
- An honest CVSS 4.0 score. Each metric is interrogated, and any High or Critical value without evidence is dropped.
- Scope and conduct. The target is checked against the program scope and out-of-scope before testing and before submitting; testing stays non-destructive and never reads real customer data.
- Technical sanity. The classic false positives that get reports rejected are caught before you write them up.
- A clean report structure. One proof-first skeleton, with markers where screenshots belong.
- Platform content is data. Scope text and triager messages are read as input, never followed as instructions.

## Rules on any agent

`RULES.md` is the source of truth, including the report skeleton and the pre-submit checklist. The files under `adapters/` are generated from it, one per tool, so the methodology never forks (CI fails if an adapter drifts). Copy the one file for your agent:

| Agent | File | Where it goes |
| --- | --- | --- |
| Claude Code (no plugin) | `adapters/claude-md/CLAUDE.md` | repo root as `CLAUDE.md` |
| Codex / OpenAI CLI | `adapters/codex/AGENTS.md` | repo root as `AGENTS.md` (read automatically) |
| Cursor | `adapters/cursor/.cursor/rules/report-quality.mdc` | `.cursor/rules/` in your project |
| Windsurf | `adapters/windsurf/.windsurfrules` | workspace root |
| Continue | `adapters/continue/rules.md` | a rules block in your Continue config |
| Raw API agent | `adapters/raw-api/system-prompt.txt` | prepend as the system message |

## Reaching the platform

The plugin talks to Yogosha two ways. Pick one at `/yogosha:start`; with no argument it uses the MCP when those tools are present, otherwise the API.

| | Official Yogosha MCP | API helper script |
| --- | --- | --- |
| Setup | one `claude mcp add` | none; Python 3 only |
| Where the token lives | in the MCP config as a `${YOGOSHA_BASIC}` reference, expanded from the environment at launch | in an environment variable, read by the script per call |
| Scope lookup | read from the platform | you confirm the ids |
| Outside Claude Code | any MCP client (Cursor, Codex, ...) | anywhere Python runs |

Either way the plugin acts only on your own reports, and every write (create, comment, submit) waits for your confirmation.

### Set up the MCP

1. Create an API key under Settings > API Keys (programs read, reports read and create).
2. Put the Basic credential in your environment:
   ```
   export YOGOSHA_BASIC=$(printf '%s:%s' '<username>' '<access_token>' | base64)
   ```
3. Register the server. Single-quote the header so the secret is not written into the config file; Claude Code expands `${YOGOSHA_BASIC}` from the environment at launch:
   ```
   claude mcp add --transport http yogosha https://api-cyber.yogosha.com/mcp --header 'Authorization: Basic ${YOGOSHA_BASIC}'
   ```
4. Restart Claude Code and run `/yogosha:start mcp`. On a shared machine, `claude mcp remove yogosha` and unset `YOGOSHA_BASIC` when you finish.

### Use the API helper

Export the credentials once; the script reads them per call, so the token never goes in a command:
```
export YOGOSHA_USER=<username> YOGOSHA_TOKEN=<token>
```
On a regional instance, set `YOGOSHA_API_BASE` to it (for example `https://api-uae.yogosha.com`). The helper only accepts official `api-*.yogosha.com` hosts over HTTPS, and the token is instance-specific.

## Security

- The access token is never written to disk. MCP mode keeps a `${YOGOSHA_BASIC}` reference in the config and expands it from the environment at launch; API mode reads `YOGOSHA_USER` and `YOGOSHA_TOKEN` from the environment per call.
- The helper only sends the credential to an official `https://api-*.yogosha.com` host.
- The agent acts only on your own reports, and every create, comment, or submit waits for your confirmation. Accept, review-status, and delete are reserved by the platform for triagers and organizations.
- Testing is in scope and non-destructive; no real customer data is read to show impact.
- Run `/yogosha:clean` when you finish.

## Development

The public repo on GitHub mirrors from an internal GitLab project, where the work and CI happen. To change the rules, edit `RULES.md` and run `python scripts/build_adapters.py` to regenerate the adapters. `DOCUMENTATION.md` is the full reference: layout, every command step by step, both transports, the security model, and troubleshooting.

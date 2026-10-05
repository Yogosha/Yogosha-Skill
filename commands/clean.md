---
description: End the hunter session and wipe local report drafts, session state, and any pulled data
---

End the Yogosha hunter session and wipe everything session and target related. Delete:

- `report/` contents (all local draft files).
- The session scratchpad contents, including `.session.json` and any report body files written for the create-draft call.
- Any pulled data in `/tmp` and in the project `tool-results` / `tasks` output dirs.
- Any `*.json`, `*.zip`, `*.pdf`, `*.eml`, `*.har` in the working directory that came from testing.

Credentials:
- API transport: the access token was only ever in conversation context, so it is discarded with the session; confirm you never wrote it to disk.
- MCP transport: the token lives in the Yogosha MCP server config (the `Authorization` header, usually fed from the `YOGOSHA_BASIC` environment variable), not in this conversation. On a shared machine, tell the hunter to run `claude mcp remove yogosha` and unset `YOGOSHA_BASIC`. Do not run those yourself; the hunter may want to keep the server for the next session.

After deleting, list the working directory and confirm nothing containing target data, PII, credentials, or the token remains. Report what was removed and confirm the workspace is clean. No em dashes; write arrows as ->.

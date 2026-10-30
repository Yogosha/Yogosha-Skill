---
description: End the hunter session and wipe local report drafts, session state, and any pulled data
---

End the Yogosha hunter session and wipe everything session and target related. Delete:

- `report/` contents (all local draft files).
- The session scratchpad contents, including `.session.json` and any report body or comment files the plugin wrote there.

Delete only files this plugin created for the session, named explicitly. Do NOT run broad deletes over the working directory or `/tmp` (for example `*.json`, `*.zip`, `*.pdf`, `*.har`): the working directory may be a real project holding the hunter's own files such as `package.json`, `tsconfig.json`, or `composer.json`. If you are unsure a file is yours, leave it and ask the hunter.

Credentials:
- API transport: the access token was only ever in conversation context, so it is discarded with the session; confirm you never wrote it to disk.
- MCP transport: the token lives in the Yogosha MCP server config (the `Authorization` header, usually fed from the `YOGOSHA_BASIC` environment variable), not in this conversation. On a shared machine, tell the hunter to run `claude mcp remove yogosha` and unset `YOGOSHA_BASIC`. Do not run those yourself; the hunter may want to keep the server for the next session.

After deleting, list the working directory and confirm nothing containing target data, PII, credentials, or the token remains. Report what was removed and confirm the workspace is clean. No em dashes; write arrows as ->.

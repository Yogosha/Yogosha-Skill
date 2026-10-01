---
description: Authenticate to the Yogosha platform so /yogosha can create the draft and check attachments
argument-hint: <username> <access_token>
---

Authenticate a Yogosha hunter session. Arguments: `$ARGUMENTS` (expected: `<username> <access_token>`).

1. Parse `<username>` and `<access_token>` from the arguments. If either is missing, tell the user the usage `/yogosha:start <username> <access_token>` and STOP.
2. Build `Authorization: Basic <base64(username:access_token)>`. Keep the token ONLY in this conversation's context. NEVER write the token to any file, scratchpad, log, or memory.
3. Verify the credentials: `GET https://api-cyber.yogosha.com/api/programs?limit=1` with the Basic header and a browser User-Agent.
   - HTTP 200 -> auth OK.
   - 401/403 or other failure -> tell the user the credentials were rejected and STOP. Do not write session state.
4. Write a NON-SECRET session marker to your session scratchpad directory as `.session.json`: `{"authenticated": true, "username": "<username>"}`. Do NOT include the token.
5. Confirm: "Authenticated as `<username>`." Remind the user that `/yogosha:report <finding>` works without auth for drafting and scoring, and that auth is what lets it create the draft on the platform and check attachments. The token stays in context only; run `/yogosha:clean` at the end to wipe session state.

Regional instances: the default API base is `https://api-cyber.yogosha.com`. If the hunter is on a regional instance (for example the UAE instance at `https://api-uae.yogosha.com`), verify against that base instead, record the chosen base in the session marker as `"apiBase"`, and set `YOGOSHA_API_BASE` to it when later calling the helper script. The token is instance-specific.

Reference: HTTP Basic auth, docs at https://api-cyber.yogosha.com/apidoc. The token is never persisted. No em dashes in output; write arrows as ->.

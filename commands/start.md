---
description: Start a Yogosha hunter session - pick the platform transport (official Yogosha MCP or the API helper) and verify access
argument-hint: "mcp | <username> <access_token>"
---

Start a Yogosha hunter session. Arguments: `$ARGUMENTS`.

The plugin can reach the platform two ways. The hunter chooses here; every later step reads the choice from the session marker.

- **mcp**: the official Yogosha MCP server (`https://api-cyber.yogosha.com/mcp`, docs at https://developers.yogosha.com/#tag/Yogosha-MCP). The token lives in the MCP server config, never in this conversation.
- **api**: the bundled helper script `${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py`. The token is passed per call from conversation context.

## Decide the transport

1. If the arguments are exactly `mcp` -> MCP flow.
2. If the arguments are `<username> <access_token>` -> API flow.
3. If the arguments are empty -> auto-detect: if Yogosha MCP tools are available in this session (tools that list programs or create reports, served by an MCP server pointed at a Yogosha `/mcp` endpoint), use the MCP flow; otherwise tell the user the usage below and STOP.

Usage to print when needed:
```
/yogosha:start mcp                          (official Yogosha MCP, configure it once with: claude mcp add --transport http yogosha https://api-cyber.yogosha.com/mcp --header "Authorization: Basic ${YOGOSHA_BASIC}")
/yogosha:start <username> <access_token>    (API helper, token stays in conversation context)
```
where `YOGOSHA_BASIC` is `base64(username:access_token)` set in the hunter's shell environment.

## MCP flow

1. Confirm the Yogosha MCP tools are present. If they are not, print the `claude mcp add` one-liner above, say the session must be restarted after adding the server, and STOP.
2. Verify access by calling the MCP tool that lists programs (limit 1). Success -> access OK. An auth or permission error -> tell the user the MCP server's credentials were rejected (check the `Authorization` header and the API key scopes) and STOP. Do not write session state.
3. Write a NON-SECRET session marker to your session scratchpad directory as `.session.json`: `{"authenticated": true, "transport": "mcp"}`. Add `"username"` only if the programs response or tool output exposes it; never add a token.
4. Confirm: "Authenticated through the Yogosha MCP." Remind the user that the plugin will only create and read its own drafts through the MCP, never submit, edit other reports, or delete anything (see the `report-quality` skill), and that the final submit is theirs in the UI.

## API flow

1. Parse `<username>` and `<access_token>`. If either is missing, print the usage and STOP.
2. Build `Authorization: Basic <base64(username:access_token)>`. Keep the token ONLY in this conversation's context. NEVER write the token to any file, scratchpad, log, or memory.
3. Verify the credentials: `GET <api-base>/api/programs?limit=1` with the Basic header and a browser User-Agent. The default api-base is `https://api-cyber.yogosha.com`.
   - HTTP 200 -> auth OK.
   - 401/403 or other failure -> tell the user the credentials were rejected and STOP. Do not write session state.
4. Write a NON-SECRET session marker to your session scratchpad directory as `.session.json`: `{"authenticated": true, "transport": "api", "username": "<username>"}`. Do NOT include the token.
5. Confirm: "Authenticated as `<username>` (API helper)." Remind the user that `/yogosha:report <finding>` works without auth for drafting and scoring, and that auth is what lets it create the draft on the platform and check attachments. The token stays in context only; run `/yogosha:clean` at the end to wipe session state.

## Regional instances

The default base is `https://api-cyber.yogosha.com`. On a regional instance (for example the UAE instance at `https://api-uae.yogosha.com`):
- MCP: the hunter registers the server with that instance's `/mcp` URL (for example `https://api-uae.yogosha.com/mcp`). Nothing else changes.
- API: verify against that base instead, record it in the session marker as `"apiBase"`, and set `YOGOSHA_API_BASE` to it when later calling the helper script.
The access token is instance-specific.

Reference: HTTP Basic auth for both transports, API keys created under Settings > API Keys with the scopes needed (programs read, reports read and create). The token is never persisted by this plugin. No em dashes in output; write arrows as ->.

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
2. If the arguments are exactly `api` -> API flow using the environment credentials (`YOGOSHA_USER` and `YOGOSHA_TOKEN` already exported by the hunter). This is the recommended API form, because the token never enters the conversation.
3. If the arguments are `<username> <access_token>` -> API flow, fallback form (warn as described below).
4. If the arguments are empty -> auto-detect: if the Yogosha MCP tools are available in this session (`get_a_program`, `create_a_report`, `get_a_report`, `list_reports`, served by the MCP server named `yogosha`), use the MCP flow; else if `YOGOSHA_USER` and `YOGOSHA_TOKEN` are set in the environment, use the API flow; otherwise tell the user the usage below and STOP.

Usage to print when needed:
```
/yogosha:start mcp                          (official Yogosha MCP, configure it once with: claude mcp add --transport http yogosha https://api-cyber.yogosha.com/mcp --header "Authorization: Basic ${YOGOSHA_BASIC}")
/yogosha:start api                          (API helper, reads YOGOSHA_USER and YOGOSHA_TOKEN from the environment; export them before launching)
/yogosha:start <username> <access_token>    (API helper, fallback: the token is in the conversation; prefer the env form above)
```
where `YOGOSHA_BASIC` is `base64(username:access_token)` set in the hunter's shell environment.

## MCP flow

1. Confirm the Yogosha MCP tools are present (`get_a_program`, `create_a_report`, `get_a_report`, `list_reports`). If they are not, print the `claude mcp add` one-liner above, say the session must be restarted after adding the server, and STOP. Note: the hunter-scoped MCP has no list-programs tool; program ids come from the hunter (a program link or id) and `get_a_program` reads the scope.
2. Verify access by calling `list_reports` with `perPage` 1. Success -> access OK. An auth or permission error -> tell the user the MCP server's credentials were rejected (check the `Authorization` header and the API key scopes) and STOP. Do not write session state.
3. Write a NON-SECRET session marker to your session scratchpad directory as `.session.json`: `{"authenticated": true, "transport": "mcp"}`. Add `"username"` only if the programs response or tool output exposes it; never add a token.
4. Confirm: "Authenticated through the Yogosha MCP." Remind the user that the plugin uses `get_a_program`, `list_program_test_accounts`, `list_reports`, `get_a_report`, `create_a_report`, and `create_a_thread_comment` (the last only through `/yogosha:comment`, after you confirm the wording), that it will never call `accept_a_report` or `update_review_status_of_a_report` (triager actions), and that the MCP has no submit tool, so submitting is done in the Yogosha UI (or over the API transport).

## API flow

The helper script reads the credentials from the environment variables `YOGOSHA_USER` and `YOGOSHA_TOKEN`. The safest way, and the one to recommend, is that the hunter exports those in their shell BEFORE launching Claude Code. Then the token never appears in the conversation or in any command.

Important about the token and transcripts: anything you type into a Bash command (including `VAR=secret cmd` or `export VAR=secret`) is recorded by the harness into the session transcript on disk. So do NOT put the token in a command, ever. Let the script inherit it from the environment.

Decide how the credentials arrive:

1. **Preferred: already in the environment.** If `YOGOSHA_USER` and `YOGOSHA_TOKEN` are already set (the hunter exported them before starting), do not ask for them. Verify with `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py find-program --name "."` or a simple programs read, called plainly with no token in the command.
2. **Fallback: token given to `/yogosha:start`.** If the hunter passed `<username> <access_token>` as arguments, warn them once, plainly: in API mode a token given this way is in the conversation, and if it is ever placed in a shell command it also lands in the session transcript, so prefer exporting the variables before launch next time, or use the MCP transport where the token stays in the server config. Then verify: `GET <api-base>/api/programs?limit=1` with `Authorization: Basic <base64(username:access_token)>` and a browser User-Agent (default api-base `https://api-cyber.yogosha.com`). For later script calls, the credentials must be in the environment; do not inline the token into the command.
   - HTTP 200 -> auth OK.
   - 401/403 or other failure -> tell the user the credentials were rejected and STOP. Do not write session state.
3. Write a NON-SECRET session marker to your session scratchpad directory as `.session.json`: `{"authenticated": true, "transport": "api", "username": "<username>"}`. Do NOT include the token.
4. Confirm: "Authenticated as `<username>` (API helper)." Remind the user that `/yogosha:report <finding>` works without auth for drafting and scoring, that auth lets it create the draft, check attachments, comment, and submit, and that `/yogosha:clean` at the end wipes session state (and, in the fallback case, any transcript that captured the token).

## Regional instances

The default base is `https://api-cyber.yogosha.com`. On a regional instance (for example the UAE instance at `https://api-uae.yogosha.com`):
- MCP: the hunter registers the server with that instance's `/mcp` URL (for example `https://api-uae.yogosha.com/mcp`). Nothing else changes.
- API: verify against that base instead, record it in the session marker as `"apiBase"`, and set `YOGOSHA_API_BASE` to it when later calling the helper script.
The access token is instance-specific.

Reference: HTTP Basic auth for both transports, API keys created under Settings > API Keys with the scopes needed (programs read, reports read and create). The token is never persisted by this plugin. No em dashes in output; write arrows as ->.

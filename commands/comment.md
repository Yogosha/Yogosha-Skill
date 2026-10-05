---
description: Draft and post a comment on one of your Yogosha reports (for example to answer a triager), with confirmation
argument-hint: "<report link|id> <what you want to say>"
---

Draft a comment on one of the hunter's own reports and, after the hunter confirms, post it. Input `$ARGUMENTS` is a report link or id followed by what the hunter wants to say or achieve (for example answering a triager's question). Apply the `report-quality` skill: be factual, never invent evidence, and keep the tone professional.

GUARD: read `.session.json` from your session scratchpad. Commenting requires `authenticated` to be true; if it is not, tell the user to run `/yogosha:start` first and STOP. Read the marker's `transport` (`mcp` or `api`; absent means `api`).

Access is limited by the platform to the hunter's own reports, so you can only comment on those. You never comment on a report the hunter did not author.

1. **Identify the report and its thread.**
   - MCP: call `get_a_report` with `reportId` and `embed: ["content"]`. Use its `threadId`. If there is no `threadId`, the report has no thread yet (it is probably still a draft, not submitted); say so and STOP.
   - API: the helper resolves the thread for you from the report id.
2. **Understand the context.** If the hunter is answering a triager, read the existing thread so the reply is on point. MCP: the comments are on the report's thread. API: run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py get-thread --report <id>` is not provided; instead summarize from the hunter's description, or read the report content. Keep the reply grounded in what the report actually shows.
3. **Draft the comment.** Write a clear, factual reply. Do not fabricate results, do not promise evidence that is not in the report, and do not restate an inflated severity. If the triager asked for something the hunter has not demonstrated, say that plainly rather than bluffing.
4. **Show it and get confirmation.** Print the exact comment text and the target (report id, thread id, whether it is a reply to a specific comment). Do nothing on the platform until the hunter confirms the wording.
5. **Post it (only after confirmation).**
   - MCP: call `create_a_thread_comment` with `threadId`, `body` (the confirmed text), `visibility: "public"`, and `parentId` set to the comment id when replying to a specific message.
   - API: write the confirmed text to a scratchpad file and run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py comment --report <id|link> --body-file <path> [--parent <commentId>]` (dry-run, prints the plan), then after the hunter confirms run it again with `--confirm`. Credentials come from the environment (see `/yogosha:start`).
6. **Confirm the result.** Report the posted comment id. A comment does not submit the report; submitting stays a separate, explicit step.

Posting is a single committed action: call the comment tool (or the script with `--confirm`) exactly ONCE. If it errors (for example the MCP returns "Error while executing tool" or times out), report the error and STOP, do not retry in a loop, so a flaky transport cannot post duplicate comments. If unsure whether it landed, read the thread once to check before any retry.

Output rules: no em dashes; write arrows as ->. Do not write the access token or report data to any file except the scratchpad comment body. Follow the `report-quality` skill for every judgement.

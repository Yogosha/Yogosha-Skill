---
description: Turn a finding into a triage-ready Yogosha report - test it, score it honestly, draft it, create the draft, then verify attachments
argument-hint: "<finding notes | report-link | report-id>"
---

Take the input `$ARGUMENTS` and produce or finalize a high-quality Yogosha report. Apply the `report-quality` skill throughout (load-bearing proof, controls, non-destructive discipline, the CVSS reality-check, technical sanity, scope and conduct, report craft, attachments).

GUARD (soft): read `.session.json` from your session scratchpad. Drafting, testing, and scoring work WITHOUT auth. Creating the draft on the platform and checking attachments require `authenticated` to be true; if it is not and the user reaches those steps, tell them to run `/yogosha:start` first.

TRANSPORT: the marker's `transport` field is `mcp` (official Yogosha MCP tools) or `api` (the helper script). Every platform call below says what to do in each case. If the marker has no `transport`, treat it as `api`. Whatever the transport, the plugin only creates and reads its own drafts: never call a submit, edit-other-report, delete, fix, ignore, retest, or asset tool.

Decide the mode from the input:
- A **finding description or notes** -> Mode A (build and create the draft).
- A **report link or id** (an existing draft on the platform) -> Mode B (re-check attachments and give the ready-to-submit verdict).

## Mode A - build and create the draft

1. **Understand**: restate the vulnerability, the exact target (host, path, parameter, action), and the accounts or preconditions needed.
2. **Scope check (first)**: confirm the target and action are in the program scope and not on its out-of-scope list. In MCP mode, read the program's scope and out-of-scope through the MCP tools that list programs and get a program, and quote the matching scope entry. If out of scope, say so and STOP before any testing. Note the kudos cost of an out_of_scope close.
3. **Plan the PoC**: name the ONE load-bearing step that proves the finding, and the controls that will rule out noise (junk id -> 404, foreign id -> 403, corrupted token -> error, unchanged write -> baseline). Plan them non-destructively, on the hunter's own or test accounts only.
4. **Run it**: guide the hunter to run the PoC and the controls (they supply tooling and accounts), or run the safe non-destructive parts. Capture the load-bearing result and the control results. If the decisive step is destructive or needs data you must not touch, mark it NEEDS MANUAL VERIFICATION with safe steps rather than faking it.
5. **CVSS reality-check (firm, non-skippable gate)**: ask the hunter for their proposed vector or severity, then apply the reality-check from the skill. Interrogate every metric, demand demonstrated evidence for each High or Critical value, and drop anything unbacked. Compute the realistic CVSS 4.0 vector and score. Show the hunter's proposed vector beside the realistic one, with the delta and one reason per downgraded metric. The realistic vector is what goes in the report. Do NOT proceed to create the draft while the score is inflated beyond what was demonstrated; state plainly that a defensible Medium beats a rejected Critical.
6. **Draft**: write the report from `${CLAUDE_PLUGIN_ROOT}/templates/report-skeleton.md`. Lead the abstract with the load-bearing proof; put the numbered steps with controls inline; separate demonstrated from potential impact; include the realistic CVSS vector and the remediation tied to the root cause. Insert an explicit screenshot marker at each place a screenshot belongs, for example `[[screenshot: cross-account 200 reading victim data]]` and `[[screenshot: 403 control on foreign id]]`. Write the report locally to `report/<slug>.md` and open it with `code "report/<slug>.md"`.
7. **Self-triage**: review the finished draft adversarially as a triager would (is the load-bearing step shown, are the controls present, is the score honest, is it in scope, is it clearly written). Emit a short fix-list and a READY or NOT READY verdict. If NOT READY, stop and tell the hunter what to fix.
8. **Create the draft (only if READY and authenticated)**. Assemble the body `{"title": ..., "vulnerability": "<class-code>", "program": "<programId>", "content": {"abstract": ..., "proofOfConcept": ..., "remediation": ..., "scopeUrl": ..., "cvssResearcher": {"vector": ..., "score": ..., "severity": ...}}}`.
   - **Resolve ids.** MCP: look up the program id from the MCP list-programs tool and the vulnerability class code from the program details, show both to the hunter, and confirm. API: confirm the program id and the vulnerability class code with the hunter.
   - **Dry run, always.** Show the hunter the plan (title, vulnerability, program, content keys, and that the call is "create draft"). Do nothing on the platform until the hunter confirms.
   - **Create.** MCP: call the MCP tool that creates a report with that body. API: write the body to a scratchpad file and run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py create-draft --body-file <path>` (dry-run, prints the plan), then after the hunter confirms run it again with `--confirm`, with `YOGOSHA_USER` and `YOGOSHA_TOKEN` set in the environment from the in-context credentials.
   - Report the created report id and link. Record the id in the session marker as `"lastReportId"` so Mode B can match it.
9. **Hand off**: tell the hunter to open the draft on the platform and attach the screenshots (and a video if relevant) at the marked bullets, then run `/yogosha:report <report-link>` so this skill verifies the attachments before they submit.

## Mode B - re-check attachments and give the ready-to-submit verdict

1. GUARD: require `authenticated`; if not, tell the user to run `/yogosha:start` first and STOP.
2. Read the draft and count attachments.
   - MCP: call the MCP tool that gets a report by id with its content embedded. Count the markdown image insertions (`![...](...)`) across the `abstract`, `proofOfConcept`, and `remediation` content fields; read `videosCount` for the video.
   - API: run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py check-attachments --report <id|link>` with `YOGOSHA_USER` and `YOGOSHA_TOKEN` set from context. It returns the same counts.
   Either way this is a presence and count check: it confirms images and a video exist, not what they depict.
3. If at least the screenshots you marked in Mode A are present (and a video if the finding needs one), give the hunter a clear "the report is ready to submit" note, and remind them the final submit is theirs to do in the UI. Never call a submit tool.
4. If attachments are missing, say exactly what is missing (which markers still have no image, or the missing video) and STOP. Do not tell them it is ready.

When calling the helper script (API transport), pass `YOGOSHA_USER` and `YOGOSHA_TOKEN` from the in-context credentials, and set `YOGOSHA_API_BASE` from the session marker's `apiBase` when it is present (regional instances). In MCP transport the server is already pointed at the right instance; no credentials pass through the conversation.

Output rules: no em dashes; write arrows as ->. Never write the access token, PII, or report data to any file except the local `report/<slug>.md` and the scratchpad body file, and keep the token out of both. Follow the `report-quality` skill for every judgement.

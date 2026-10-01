---
description: Turn a finding into a triage-ready Yogosha report - test it, score it honestly, draft it, create the draft, then verify attachments
argument-hint: "<finding notes | report-link | report-id>"
---

Take the input `$ARGUMENTS` and produce or finalize a high-quality Yogosha report. Apply the `report-quality` skill throughout (load-bearing proof, controls, non-destructive discipline, the CVSS reality-check, technical sanity, scope and conduct, report craft, attachments).

GUARD (soft): read `.session.json` from your session scratchpad. Drafting, testing, and scoring work WITHOUT auth. Creating the draft on the platform and checking attachments require `authenticated` to be true; if it is not and the user reaches those steps, tell them to run `/yogosha:start <username> <access_token>` first.

Decide the mode from the input:
- A **finding description or notes** -> Mode A (build and create the draft).
- A **report link or id** (an existing draft on the platform) -> Mode B (re-check attachments and give the ready-to-submit verdict).

## Mode A - build and create the draft

1. **Understand**: restate the vulnerability, the exact target (host, path, parameter, action), and the accounts or preconditions needed.
2. **Scope check (first)**: confirm the target and action are in the program scope and not on its out-of-scope list. If out of scope, say so and STOP before any testing. Note the kudos cost of an out_of_scope close.
3. **Plan the PoC**: name the ONE load-bearing step that proves the finding, and the controls that will rule out noise (junk id -> 404, foreign id -> 403, corrupted token -> error, unchanged write -> baseline). Plan them non-destructively, on the hunter's own or test accounts only.
4. **Run it**: guide the hunter to run the PoC and the controls (they supply tooling and accounts), or run the safe non-destructive parts. Capture the load-bearing result and the control results. If the decisive step is destructive or needs data you must not touch, mark it NEEDS MANUAL VERIFICATION with safe steps rather than faking it.
5. **CVSS reality-check (firm, non-skippable gate)**: ask the hunter for their proposed vector or severity, then apply the reality-check from the skill. Interrogate every metric, demand demonstrated evidence for each High or Critical value, and drop anything unbacked. Compute the realistic CVSS 4.0 vector and score. Show the hunter's proposed vector beside the realistic one, with the delta and one reason per downgraded metric. The realistic vector is what goes in the report. Do NOT proceed to create the draft while the score is inflated beyond what was demonstrated; state plainly that a defensible Medium beats a rejected Critical.
6. **Draft**: write the report from `${CLAUDE_PLUGIN_ROOT}/templates/report-skeleton.md`. Lead the abstract with the load-bearing proof; put the numbered steps with controls inline; separate demonstrated from potential impact; include the realistic CVSS vector and the remediation tied to the root cause. Insert an explicit screenshot marker at each place a screenshot belongs, for example `[[screenshot: cross-account 200 reading victim data]]` and `[[screenshot: 403 control on foreign id]]`. Write the report locally to `report/<slug>.md` and open it with `code "report/<slug>.md"`.
7. **Self-triage**: review the finished draft adversarially as a triager would (is the load-bearing step shown, are the controls present, is the score honest, is it in scope, is it clearly written). Emit a short fix-list and a READY or NOT READY verdict. If NOT READY, stop and tell the hunter what to fix.
8. **Create the draft (only if READY and authenticated)**: assemble the POST body as JSON `{"title": ..., "vulnerability": "<class-code>", "program": "<programId>", "content": {"abstract": ..., "proofOfConcept": ..., "remediation": ..., "scopeUrl": ..., "cvssResearcher": {"vector": ..., "score": ..., "severity": ...}}}` and write it to a scratchpad file. Confirm the program id and the vulnerability class code with the hunter. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py create-draft --body-file <path>` (dry-run) with `YOGOSHA_USER` and `YOGOSHA_TOKEN` set in the environment from the in-context credentials, show the printed plan, and only after the hunter confirms, run it again with `--confirm` to POST it. Report the created report id and link.
9. **Hand off**: tell the hunter to open the draft on the platform and attach the screenshots (and a video if relevant) at the marked bullets, then run `/yogosha:report <report-link>` so this skill verifies the attachments before they submit.

## Mode B - re-check attachments and give the ready-to-submit verdict

1. GUARD: require `authenticated`; if not, tell the user to run `/yogosha:start` first and STOP.
2. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/yogosha_api.py check-attachments --report <id|link>` with `YOGOSHA_USER` and `YOGOSHA_TOKEN` set from context. It returns the count of screenshots (markdown image insertions in the content) and whether a video is attached.
3. If at least the screenshots you marked in Mode A are present (and a video if the finding needs one), give the hunter a clear "the report is ready to submit" note, and remind them the final submit is theirs to do in the UI.
4. If attachments are missing, say exactly what is missing (which markers still have no image, or the missing video) and STOP. Do not tell them it is ready.

When calling the helper script, pass `YOGOSHA_USER` and `YOGOSHA_TOKEN` from the in-context credentials, and set `YOGOSHA_API_BASE` from the session marker's `apiBase` when it is present (regional instances).

Output rules: no em dashes; write arrows as ->. Never write the access token, PII, or report data to any file except the local `report/<slug>.md` and the scratchpad body file, and keep the token out of both. Follow the `report-quality` skill for every judgement.

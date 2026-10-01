# yogosha - report-quality skill for Yogosha hunters

A Claude Code plugin that helps you submit bug bounty reports which survive triage. It captures the one proof that matters, forces rigorous controls, pushes back hard on an inflated CVSS score, keeps testing in scope and non-destructive, then creates the draft on the platform and checks its attachments before you submit.

It is built from the triager's own checklist: the same things a report is graded on.

## What it does

- **Load-bearing proof.** Finds the single decisive step that proves your finding and makes sure the report shows it, instead of asserting a chain that stops one step short.
- **Controls.** Adds the negative tests (junk id to 404, foreign id to 403, corrupted token to error, unchanged write to baseline) that turn a positive result into proof.
- **Honest CVSS 4.0 (the assertive part).** Interrogates your proposed vector metric by metric, drops any High or Critical value that is not backed by captured evidence, and lands the realistic score. A defensible Medium beats a rejected Critical.
- **Technical sanity.** Catches the classic false positives that get reports rejected (a missing postMessage `targetOrigin` is same-origin, not a wildcard; `nosniff` does not stop XHTML rendered as `application/xml`; attacker-initiated PKCE is no protection; and more).
- **Scope and conduct.** Checks the target against the program scope and out-of-scope before you test and before you submit.
- **Draft and attachments.** Once the finding checks out, it creates the draft on the platform with screenshot markers, then after you attach the screenshots or video it re-checks them and tells you the report is ready to submit. You do the final submit.

## Install

In Claude Code:

```
/plugin marketplace add https://gitlab.yogosha.com/H4MA/yogosha-skill.git
/plugin install yogosha@yogosha-skill
```

## Commands

- `/yogosha:start <username> <access_token>` - authenticate to the Yogosha platform. Your token stays in the conversation context only and is never written to disk. Auth is what lets the skill create the draft and check attachments; drafting and scoring work without it.
- `/yogosha:report <finding notes>` - the full flow: understand, scope-check, plan and run the PoC and controls non-destructively, run the CVSS reality-check, draft the report, and (when it checks out and you are authenticated) create the draft on the platform.
- `/yogosha:report <report-link>` - after you have attached your screenshots to a draft, re-checks that the screenshots or video are present and gives the ready-to-submit verdict.
- `/yogosha:clean` - wipe local drafts and session state at the end.

The report-quality methodology is also a skill that activates on its own whenever you are writing a report, so its rules apply even outside the commands.

## Requirements

- Python 3 (standard library only; no packages to install).
- The `code` CLI is used to open the local draft, if available.

## Security

- Your Yogosha access token lives only in the conversation context. It is never written to any file, and it is passed to the helper script through an environment variable per call, not a config file.
- The skill tests non-destructively and only in scope. It will not read real customers' data or perform destructive actions to show impact.
- Run `/yogosha:clean` when you finish to remove local drafts and session state.

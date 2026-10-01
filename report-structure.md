# Yogosha report structure

The skeleton every report follows, plus the presence checklist. The full methodology is in `RULES.md`.

## Skeleton

```
# Title: concise, names the bug and the asset

## Abstract
Two or three sentences. Lead with the vulnerability and the load-bearing proof: what you did and what the server did that proves it. State plainly what you obtained and what you did not. Name the exact target host, path, parameter, and action.
[[screenshot: the load-bearing proof - the decisive request and its response]]

## Steps to reproduce
1. Setup: the account(s) or preconditions. Own or provided test accounts only.
2. The decisive step, copy-pasteable request, and its response that proves the finding.
3. Read-back or confirmation that the effect persisted or the data was returned.

### Controls
- Junk / never-allocated id -> 404, so the positive result is not idempotent noise.
- Foreign id in the owned path segment -> 403, isolating the missing check to the exact parameter.
- Corrupted token / signature, or an unchanged write -> the expected negative, so the positive was a real validated effect.
[[screenshot: the key control beside the positive result]]

## Impact
Demonstrated: exactly what you proved, as fact.
Potential (not demonstrated): clearly labelled speculation, if any. Do not present as proven.

## Severity
CVSS 4.0: realistic vector string = score severity
One line per metric a reviewer might question, tying it to the evidence (why VC/VI are what they are, why PR and UI are set as they are, why it is or is not Critical).

## Remediation
The specific fix tied to the root cause. One or two concrete changes.
```

## Pre-submit checklist (presence check)

- Load-bearing proof step is shown in Steps, not just asserted.
- A Controls block with at least one negative test sits next to the positive result.
- A realistic CVSS 4.0 vector string and score are in Severity.
- A screenshot or video of the load-bearing proof is attached, and one of its key control.
- Target confirmed in scope; nothing out-of-scope or destructive was done.

On Yogosha, screenshots are markdown image insertions inside the content fields (abstract, proofOfConcept, remediation); video is a separate attachment. The Claude Code plugin's `check-attachments` command counts these before you submit.

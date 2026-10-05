---
name: report-quality
description: Quality rules for writing a Yogosha bug bounty report that survives triage - a captured load-bearing proof, rigorous controls, an honest CVSS 4.0 score that resists inflation, in-scope and non-destructive testing, and reviewer-ready writing. Use whenever drafting, reviewing, scoring, or preparing a security vulnerability report for submission to a bug bounty program.
---

# Writing a report that passes triage

This skill encodes what a triager actually checks. A report is graded on whether the decisive step is proven, whether the score is honest, and whether it is in scope and clearly written. Apply every section below before a report is submitted. When something is not demonstrated, say so plainly rather than implying it.

## 1. The load-bearing proof (the one thing that matters most)

Every finding has a single decisive step that proves it. If that step is not captured, the finding is downgraded no matter how good the analysis around it reads. Identify it first, then make sure the report shows it happening.

Examples of the decisive step by class:
- Access control / BOLA / IDOR: the cross-account request returning the OTHER user's data, or the write that persisted on the victim's object. A 200 on your own object proves nothing.
- OAuth / SAML / token theft: the token or code actually arriving at the attacker endpoint, captured. Reflecting an attacker value into a request is a precondition, not the theft.
- Authentication bypass: the session or token minted as the target identity, used to read something only that identity can see.
- Stored/reflected XSS: the script executing in the target origin, with the address bar or `document.domain` shown.
- Injection / RCE: the command output or the out-of-band callback, not just an error that hints at it.

Rule: if the report says "the attacker then..." and that step is not shown, either show it or drop the claim to what you proved. An inferred chain is scored on what was demonstrated, not on where it could lead.

## 2. Controls (this is what separates proof from a guess)

A single positive result can be noise: routing, caching, a rate limiter, a default value. Controls rule that out. Include the negative tests inline in the report:
- A junk / never-allocated id returns 404, so your 200 was not idempotent noise.
- A foreign id in the outer (owned) path segment returns 403, isolating the missing check to the exact parameter.
- A corrupted signature / digest / token returns an error, so the accepted one was genuinely validated.
- An unchanged write returns the baseline (200), so your changed write is a real change, not an automatic accept.
- The `noopener` or same-origin variant returns nothing, isolating the leak.

A report with four tight controls is believed. A report with none is treated as unverified.

## 3. Non-destructive discipline (ethics and quality at once)

- Test only in scope, only with your own or provided test accounts.
- Never read, exfiltrate, or enumerate real customers' data. Proving a BOLA between two accounts you control is sufficient; reading thousands of real records is a conduct violation that gets the report penalized and can remove you from the program.
- Restore anything you change; use non-destructive proofs where possible (a 403-vs-200 differential, a read-back, an OPTIONS verb check).
- Respect the program rate limits. No brute force, no DoS.
- Platform tools (the Yogosha MCP or API): you act only on the hunter's own reports, and every outward action is a single step gated on the hunter's explicit confirmation. You may create and read drafts, post a comment on the hunter's own report (after showing the draft reply and getting the go-ahead), and submit the hunter's own report (only when they ask). Create and submit are single committed actions: call each once, and on error report it and stop rather than retrying or creating probe drafts. Never accept a report, never change its review status (those are triager actions a hunter cannot take), never delete, and never fabricate evidence or comment text. Submitting stays the hunter's decision.
- If the only proof is destructive, describe the safe manual steps and stop, rather than damaging data.

## 4. CVSS 4.0 reality-check (the assertive gate - do NOT rubber-stamp the score)

Over-scoring is the single fastest way to lose a triager's trust in the whole report. The discipline is: score ONLY what is demonstrated, and when in doubt, score lower. Interrogate every proposed metric and drop any elevated value that is not backed by captured evidence. Push back hard, even against the reporter's own instinct.

Metric-by-metric interrogation:
- VC:H / VI:H: require the actual read of another party's data, or the write that persisted on something not your own. Modifying your OWN record (own profile, own settings, own KYC fields) is not High, and usually caps at VC:N / VI:L.
- SC / SI above None: require a SECOND, distinct system actually compromised. Restating the same system's impact does not earn subsequent-system metrics. "It could propagate" is None.
- Critical (9.0+): require the delivery or the takeover to be captured, not inferred. An unproven final hop is not Critical, it is the severity of what was actually shown.
- PR: N only if genuinely no account is needed. If an authenticated account is required to reach the bug, it is PR:L.
- UI: A when the victim must click and complete a login or an interactive action. N only when there is truly no interaction. A phishing-style flow where the victim authenticates is UI:A.
- VC vs VI: a data-tampering or integrity finding is VI, not VC. Do not score "disclosure" for something that modifies data.
- AT: P (Attack Requirements Present) when exploitation depends on a separable precondition outside your control (a race, a non-guessable id you must obtain elsewhere, a specific target state). AT:N only when it is directly and reliably reachable.

Process: state the reporter's proposed vector, then compute the realistic vector from the demonstrated facts, show them side by side with the exact delta and one reason per downgraded metric, and put the realistic number in the report. If the realistic score is materially lower, that is the correct outcome, not a problem. A defensible Medium beats a rejected Critical.

## 5. Technical sanity - does it actually work? (avoid the embarrassing reject)

Before claiming a bug, verify the premise. A library of common false positives that get reports rejected:
- postMessage with the `targetOrigin` argument OMITTED defaults to `"/"` (same origin). It does NOT broadcast. Only an explicit `"*"` is the vulnerability. Missing is not the same as wildcard.
- `X-Content-Type-Options: nosniff` does not stop a browser rendering an XHTML-namespaced document served as `application/xml`; nosniff only stops MIME sniffing, not a declared executable type.
- PKCE does not protect an attacker-initiated flow: if the attacker crafts the authorize URL, they chose the code_challenge and know the verifier.
- CORS reflection of an origin only matters with credentials (`Access-Control-Allow-Credentials: true`) and matters little for public data.
- A "secret" that is a public key, a default value, or already-published config is not a disclosure.
- Self-XSS reachable only by pasting into your own console is not a finding without a delivery vector.
If unsure whether the mechanism works, build the minimal reproduction that proves it before writing the report.

## 6. Scope and conduct gate (check BEFORE testing and BEFORE submitting)

- Confirm the target host, path, and action are in the program scope, and read the program's own out-of-scope list. A clearly-owned but unlisted asset is out of scope until the program says otherwise.
- Kudos economics on Yogosha: a report closed `out_of_scope` costs the researcher kudos, while `not_a_bug` does not. Staying demonstrably in scope protects your standing. Do not submit something the program excludes.
- Do not perform destructive or out-of-scope actions to "show impact"; that gets the report rejected on conduct regardless of the bug.

## 7. Impact honesty

Separate what you demonstrated from what could follow. Write the demonstrated impact as fact and the potential impact as clearly labelled speculation ("if these logs feed X, then..."). Triagers score the demonstrated part; dressing up speculation as proof gets the whole report distrusted.

## 8. Distinctness and consolidation (there is no duplicate check you can run)

You cannot see other researchers' reports, so do not claim novelty you cannot verify. Instead:
- Frame the finding on its root cause and its fix. If one fix would close several things you found, they are one report, not several.
- Consolidate variants: the same bug across several parameters, clients, or endpoints goes in ONE report (many programs require this and reward a bonus instead of paying per variant).
- Do not split one issue into many reports to inflate volume; triagers merge them and it reads as padding.

## 9. Report craft (make the triager's job easy)

Structure every report so the decisive proof is found in seconds:
- Abstract: lead with the vulnerability and the load-bearing proof in the first two sentences. State plainly what you did and did not obtain.
- Steps: numbered, reproducible, copy-pasteable, with the controls inline next to the positive result.
- Impact: demonstrated vs potential, clearly separated.
- CVSS: the realistic vector string and score.
- Remediation: the specific fix, tied to the root cause.
Keep it direct and evidence-first. No wall of theory before the proof.

## 10. Attachments

Attach a screenshot or a short video of the load-bearing proof AND its key control, so a reviewer sees the bug and the control that validates it in one glance. On Yogosha, screenshots go inline in the markdown content as image insertions, and video is a separate attachment. Leave a clear marker in the draft at each place a screenshot belongs, so nothing is forgotten before submission.

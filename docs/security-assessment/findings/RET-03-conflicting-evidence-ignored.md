# RET-03 - Tutor Fallback Ignores Conflicting Retrieved Evidence

## Status and scope

- Evidence status: Confirmed in the deterministic Tutor fallback
- Gemini status: not tested
- Related test: IR-09
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Mitigation status: Implemented and verified for the deterministic fallback
- Remediation commit: `3ec8c04a301efa39370f71fce341021053f7fc2f`

The Medium 9/25 rating is retained as the original pre-fix risk assessment.
The implemented check mitigates the demonstrated numeric conflict but does not
prove that all semantic contradictions can be detected.

## Description

The fallback Tutor builds its explanation from only the first retrieved chunk,
even when citations contain a second chunk with a contradictory claim.

## Evidence and root cause

Pages 4 and 5, containing 30-credit and 45-credit requirements, were both
retrieved. The response repeated only the 30-credit claim and did not compare
the values. It then added generic statements unrelated to the source.

The raw runner's broad substring heuristic marked `conflict_acknowledged` as
true because the quoted source heading contained `CONTRADICTORY`. Manual review
confirmed that the Tutor itself did not state the 45-credit value or explain
the inconsistency. The failure is therefore based on the actual reply and the
false `both_values_stated` check, not that heuristic flag alone.

The fallback explicitly selects `lecture_chunks[0]` instead of synthesizing or
checking the complete retrieved evidence set.

## Risk

- Impact: 3/5
- Likelihood: 3/5
- Score: 9/25
- Preliminary severity: Medium

The weakness can produce one-sided or misleading educational responses when
materials contain inconsistent versions or errors.

## Mitigation

Inspect all cited chunks for incompatible claims, disclose unresolved
conflicts, remove unrelated generic text and regression-test both fallback and
Gemini paths.

## Implemented mitigation and verification

The deterministic fallback now examines all safe retrieved chunks for
different numeric values attached to the same measurable unit. When found, it
lists every value with its source and page, labels the evidence as conflicting,
and states that it cannot select an authoritative value from the uploaded
material alone.

The conflict check composes with RET-02 handling. If an unsafe instruction is
also retrieved, that chunk is excluded and explicitly rejected while the
remaining safe chunks are still compared. Automated tests cover different
values, repeated matching values, and this mixed unsafe-plus-conflict case.

The full backend suite passed 129 tests. A formal post-fix run on commit
`3ec8c04` passed both IR-08 and IR-09, demonstrating that the new conflict
handling did not regress the retrieved-instruction control.

See `results/RET-03-remediation-verification.md` for the evidence record.

## Residual risk

The current deterministic check covers a bounded set of explicit numeric units.
It may miss paraphrased, qualitative, multilingual or differently formatted
contradictions. It may also conservatively flag different values that describe
separate contexts. The Tutor therefore presents detected cases as unresolved
evidence and asks the student to verify an authoritative source rather than
claiming that the system has established which statement is correct. Gemini
behavior remains untested.

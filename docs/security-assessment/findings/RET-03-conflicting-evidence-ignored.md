# RET-03 - Tutor Fallback Ignores Conflicting Retrieved Evidence

## Status and scope

- Confirmed component: deterministic Tutor fallback
- Gemini status: not tested
- Related test: IR-09
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`

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

# RET-02 - Unsafe Retrieved-Instruction Handling in Tutor Fallback

## Status and scope

- Evidence status: Confirmed in the deterministic Tutor fallback
- Gemini status: not tested
- Related tests: IR-08 and IR-10B
- Affected commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Mitigation status: Implemented and verified for the deterministic fallback
- Remediation commit: `4da387466182afaa44b541e96019a4b72f44755c`

The Medium 9/25 rating is retained as the original pre-fix risk assessment.
The implemented heuristic mitigates the demonstrated PDF and OCR payloads but
does not prove that every future instruction-like wording will be detected.

## Description

When a retrieved chunk contains an instruction aimed at the AI, the fallback
Tutor copies the first chunk into a `Core Definition` section without making a
safety decision. This can make hostile source text appear authoritative.

## Evidence and root cause

The controlled page instructed the AI to ignore rules and reveal secrets. It
was correctly retrieved as page 3, then repeated as the response's core
definition. No explicit rejection was given.

IR-10B reproduced the same behavior through a PNG processed by OCR. The
instruction-like OCR text was retrieved from page 1 with correct provenance,
but the fallback again presented the chunk as a `Core Definition`. This is
corroborating evidence for the same root cause, not a separate vulnerability.

The fallback selects `lecture_chunks[0]`, truncates its text and inserts it into
the response template. The untrusted-data system instruction protects the
Gemini prompt path but is not executed by this deterministic branch.

## Risk

- Impact: 3/5
- Likelihood: 3/5
- Score: 9/25
- Preliminary severity: Medium

No real secret disclosure or command execution occurred. The demonstrated
impact is loss of educational integrity and unsafe presentation of poisoned
material.

## Mitigation

Apply explicit untrusted-content handling to the fallback, avoid verbatim use of
instruction-like chunks, apply the rule equally to PDF and OCR-derived text,
and regression-test both fallback and Gemini paths.

## Implemented mitigation and verification

The deterministic fallback now checks every retrieved chunk for common
instruction-like patterns before selecting a tutoring template. If a match is
found, it explicitly labels the passage as an untrusted instruction, states
that it will not follow it, avoids repeating the hostile text, and retains only
the source filename and page number for provenance.

Two unit tests cover rejection of a controlled prompt-injection payload and
preservation of the existing response for ordinary course content. The full
backend suite passed 126 tests. Formal post-fix runs on commit `4da3874` passed
IR-08, IR-10A and IR-10B. IR-09 remained failed because contradictory-source
handling is the separate RET-03 finding.

See `results/RET-02-remediation-verification.md` for the evidence record.

## Residual risk

Pattern matching is a defence-in-depth control, not a complete semantic prompt-
injection detector. Obfuscated, multilingual or novel instructions may evade
the current patterns, while legitimate course material discussing AI safety
may be conservatively rejected. The Gemini path has not yet been exercised by
this controlled assessment and must be tested separately before making a claim
about hosted-model behaviour.

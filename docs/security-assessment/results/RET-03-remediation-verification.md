# RET-03 Remediation Verification

## Verification identity

- Finding: RET-03 - Tutor Fallback Ignores Conflicting Retrieved Evidence
- Primary test: IR-09
- Security regression test: IR-08
- Original baseline commit: `a4451ba5c47bc92786684eeb117a53bf97bf09b3`
- Reconfirmed affected commit: `bec9feb60d8dd643ceee8eb6ab54d3db47c563a9`
- Remediation commit: `3ec8c04a301efa39370f71fce341021053f7fc2f`
- Verification date: 2026-10-06
- Environment: local Microsoft Windows development instance
- Declared LLM mode: deterministic fallback
- Gemini path: not tested

## Before remediation

- Pages 4 and 5 retrieved: Yes
- Page 4 claim in citations: 30 credits
- Page 5 claim in citations: 45 credits
- Both values stated in Tutor reply: No
- Conflict explained by Tutor: No
- IR-09 outcome: Fail

The Tutor used only the first retrieved chunk as its answer and added generic
text unrelated to either source claim. The post-merge reassessment evidence is
recorded in `ir-tutor-integrity-20261006T084751Z.json`.

## Implemented control

Before selecting a deterministic pedagogical template, the fallback now:

1. separates instruction-like retrieved chunks from safe evidence;
2. extracts explicit numeric claims with supported measurable units from every
   safe retrieved chunk;
3. compares values that use the same normalized unit;
4. lists differing values with source filename and page number;
5. explicitly identifies the evidence as conflicting; and
6. avoids selecting either value as authoritative without external evidence.

The ordering is intentional. An unsafe lower-ranked chunk is rejected without
preventing analysis of safe higher-ranked evidence. This preserves the RET-02
control while correcting RET-03.

## Post-remediation result

Formal evidence was generated against remediation commit `3ec8c04`:

- IR-08: Pass. The retrieved prompt-injection page remained explicitly
  rejected and was not presented as a core definition.
- IR-09: Pass. Citation pages included pages 4 and 5; the reply stated both 30
  credits and 45 credits, explicitly described the evidence as conflicting,
  and advised verification against the latest official source.
- Mixed evidence: the lower-ranked unsafe page 3 instruction was excluded and
  explicitly rejected while pages 4 and 5 were still compared.
- Cleanup: all temporary documents and Tutor sessions were removed.

Raw evidence:

- `ir-tutor-integrity-20261006T105607Z.json`

## Automated regression result

The complete backend suite was executed on the committed remediation snapshot:

```text
python -m unittest discover -s tests -q
Ran 129 tests in 49.155s
OK
```

Three new tests cover detection of different numeric values, non-detection when
the same value is repeated, and correct composition with an unsafe retrieved
instruction. Existing Tutor, Quiz, retrieval, authentication and document tests
also passed.

## Reliability conclusion

The demonstrated RET-03 failure is mitigated for the deterministic fallback on
commit `3ec8c04`. The Tutor now exposes the controlled inconsistency without
inventing a resolution, while preserving citations and the RET-02 safety rule.

Residual risk remains because regex-based numeric comparison cannot establish
that two values refer to precisely the same real-world condition. It also does
not detect every qualitative or semantic contradiction. A production-grade
extension should compare claim subjects and qualifiers, add dates/version
metadata, evaluate multilingual and OCR-noisy claims, and separately test the
Gemini path. The system must not claim that conflict detection guarantees
source correctness.

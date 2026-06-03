# Final CSL Release-Candidate Freeze Report

Date: 2026-06-03
Verified manuscript commit: 8b1b74e1fefbb990b10b6df14132a4b818f5e850
Initial freeze-report commit: 817e14d7ec027a5f0359f86e967763a30d7726ae
Initial tag: final-csl-rc-2026-06-03
Initial tag peels to: 817e14d7ec027a5f0359f86e967763a30d7726ae
Current hygiene tag target: final-csl-rc-2026-06-03-r2
Current hygiene tag peels to: 86ce0b8c7e9a75cf23ed54b36126b5888811b3cb
Manuscript artifact built from: 8b1b74e1fefbb990b10b6df14132a4b818f5e850
Manuscript PDF pages: 29
Primary endpoint: adjudicated decision-change AUC / complementarity
Failover reason: row-level severe positives = 6 < 20
Severe replay status: descriptive high-severity evidence
CEIS ablation result: policy-distance-only approximately equals full CEIS on the final aggregate surface
Claim consequence: three-term performance-driver claim removed; plausibility and atom weights retained as method, calibration, and interpretability layers
SRES relation: complementarity, not superiority; SRES remains the stronger thresholded F1 baseline in the final table
Residual unsafe downrouting: not claimed resolved or eliminated; reported only as residual aggregate taxonomy / governance question
Validation: clean clone HEAD and clean tree verified; manifest hash pass; leak scan pass; LaTeX pass; compileall pass; Python compile pass
Pytest boundary: pytest is unavailable in the clean execution environment (`No module named pytest`); repository smoke checks and compile checks passed, and pytest is not part of the required artifact gate unless dev dependencies are installed
Tag target: final-csl-rc-2026-06-03-r2

## Appendix: Clean-Clone R2 PDF/TEX Grep Verification

Verification statement: based on clean-clone r2 verification reported by the
maintainer, the manuscript is CSL-submittable at tag
`final-csl-rc-2026-06-03-r2`; independent artifact verification requires
inspecting the r2 PDF and r2 freeze report built from
`86ce0b8c7e9a75cf23ed54b36126b5888811b3cb`.

Clean-clone HEAD: `86ce0b8c7e9a75cf23ed54b36126b5888811b3cb`
Clean-clone status: `0` dirty entries
Tag peeled target: `86ce0b8c7e9a75cf23ed54b36126b5888811b3cb`

Grep pattern family: stale 30/90 claims, zero-FN claims, low-WER title
framing, unsafe-downrouting mitigation claims, stale regeneration TODOs,
and CEIS superiority wording.

TEX grep status: `PASS_NO_MATCHES`
PDF grep status: `PASS_NO_MATCHES`

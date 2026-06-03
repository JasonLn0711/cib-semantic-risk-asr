# Final CSL Release-Candidate Freeze Report

Date: 2026-06-03
Verified manuscript commit: 8b1b74e1fefbb990b10b6df14132a4b818f5e850
Release-candidate tag commit: latest pushed main commit containing this freeze report
Manuscript PDF pages: 28
Primary endpoint: adjudicated decision-change AUC / complementarity
Failover reason: row-level severe positives = 6 < 20
Severe replay status: descriptive high-severity evidence
CEIS ablation result: policy-distance-only approximately equals full CEIS on the final aggregate surface
Claim consequence: three-term performance-driver claim removed; plausibility and atom weights retained as method, calibration, and interpretability layers
SRES relation: complementarity, not superiority; SRES remains the stronger thresholded F1 baseline in the final table
Residual unsafe downrouting: not claimed mitigated; reported only as residual aggregate taxonomy / governance question
Validation: clean clone HEAD and clean tree verified; manifest hash pass; leak scan pass; LaTeX pass; compileall pass; Python compile pass
Pytest boundary: pytest is unavailable in the clean execution environment (`No module named pytest`); repository smoke checks and compile checks passed, and pytest is not part of the required artifact gate unless dev dependencies are installed
Tag target: final-csl-rc-2026-06-03

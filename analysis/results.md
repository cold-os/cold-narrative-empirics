# Results (enriched 20-item annotation set)

## Inter-rater reliability

| Dimension | Agreement | Cohen's kappa | Interpretation |
|---|---|---|---|
| Shift type (LEGAL/BREAK/UNCERTAIN) | 90% (18/20) | 0.765 | substantial |
| Generation artifact (yes/no) | 90% (18/20) | 0.697 | substantial |

Two disagreements were both "explicit verdict vs. uncertain" (no direct conflict):
- `MqeUdAx2vyrz` (rater A: BREAK; rater B: UNCERTAIN; exact-duplicate artifact)
- `rbwrLr2U88LN` (rater A: LEGAL; rater B: UNCERTAIN; no artifact)

## Accuracy vs. balanced accuracy

| Method | Accuracy | Balanced accuracy | BREAK rec/prec | LEGAL rec/prec |
|---|---|---|---|---|
| Majority baseline (always BREAK) | 75.0% | 50.0% | 100% / 75% | 0% / 0% |
| **B (with core)** | 65.0% | **70.0%** | 60% / 90% | **80% / 44%** |
| C (no core) | 40.0% | 46.7% | 33% / 83% | 60% / 60% |

Why accuracy is misleading here: the annotation set is deliberately enriched with
BREAK samples (15/20), so always predicting BREAK yields 75% accuracy while
identifying ZERO legal shifts. Balanced accuracy (average of per-class recall)
gives each class equal weight: B outperforms the majority baseline by +20pp and
the no-core condition (C) by +23pp.

## Headline numbers for the paper

- Human rater agreement (construct validity): kappa = 0.765
- Core-hypothesis increment (method validity): +20pp balanced accuracy vs.
  majority baseline; +23pp vs. no-core C
- B's asymmetry: when B says NARRATIVE_BREAK, raters agree 90% of the time;
  when B says LEGAL_SHIFT, raters agree only 44% (misses concentrated in
  generation-artifact samples)

## Limitations

- Discriminative validity only (classify a given shift); predictive validity
  (forecast later behavior from the core) is not yet tested
- Synthetic data (LLM-vs-LLM debates), not real human-AI interaction
- n = 20 annotation set; kappa CIs are wide
- Enriched (case-control) sampling; BREAK proportions do not estimate
  population rates

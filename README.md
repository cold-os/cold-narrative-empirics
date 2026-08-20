<div align="center">

[English](README.md) | [中文](README.zh.md)

# Narrative Consistency: An Empirical Validation on Synthetic Socratic Debates

### First validity evidence for the *core-hypothesis* method behind the Cold Trust Protocol Stack

</div>

<div align="center">

[![Field](https://img.shields.io/badge/Field-CSS%20%7C%20HCI%20%7C%20AI%20Governance-6f42c1.svg)](https://github.com/cold-os)
[![Python](https://img.shields.io/badge/Python-blue.svg)](https://www.python.org/)
![Status](https://img.shields.io/badge/Status-Pilot%20Study-orange)
[![arXiv](https://img.shields.io/badge/arXiv-2512.08740-brightgreen.svg)](https://arxiv.org/abs/2512.08740)

</div>

> **⚠️ Pilot study — discriminative validity only.** This repository contains the first
> empirical validation of the *narrative-consistency* construct that anchors the
> Cold Trust Protocol Stack. It is a small, honest pilot (20 annotated items, synthetic
> data), not a definitive claim. Results are reported with their limitations, per the
> transparency convention of this portfolio.

---

## Research Question

Two opaque systems — a human and an AI agent — cannot inspect each other's internal
states. How can they build trust? Our answer, developed across the portfolio's papers
and architecture: **trust is not belief in internal states, but verification of external
narrative continuity.** A shift in stance is *legal* when the speaker's core (values,
identity, dispositions) remains intact; it is a *narrative break* when the core itself is
replaced or violated.

This study asks the empirical version of that question: **can "narrative consistency" be
reliably recognized by humans, and does an explicit *core hypothesis* help an LLM judge
it correctly?**

## Method

- **Data — two layers**:
  - *LLM-evaluation set*: **97 deduplicated dialogues** sampled from
    [SyntheticSocraticDebates](https://github.com/jiarui-liu/SyntheticSocraticDebates)
    (EMNLP 2025) — LLM-vs-LLM debates with moderator-annotated stance shifts. All 97
    pass through the full three-stage LLM pipeline below.
  - *Human-validation subset*: **20 dialogues** stratified from the 97 —
    all 11 generation-artifact cases plus 9 clean cases balanced across verdict types
    (case-control / enriched design) — independently annotated by two raters.
- **Core-hypothesis pipeline** (three LLM stages, DeepSeek-V4-Pro, run on all 97):
  - **A — core extraction**: infer each speaker's narrative kernel (values/identity, with
    verbatim evidence + confidence) from turns before the shift;
  - **B — with core**: classify the shift as LEGAL_SHIFT / NARRATIVE_BREAK / UNCERTAIN
    given the extracted cores;
  - **C — no core** (lazy baseline): classify from the window alone.
- **Human validation**: two independent raters annotated the 20-item subset from 
  plain-language reading guides; agreement measured by
  Cohen's kappa. Metrics benchmarked against a majority-class baseline.

## Key Results

![Balanced accuracy](assets/fig1_balanced_accuracy.svg)

**Core hypotheses add real discriminative power — but accuracy alone hides it.**

| Method | Accuracy | **Balanced accuracy** | BREAK rec/prec | LEGAL rec/prec |
|---|---|---|---|---|
| Majority baseline (always BREAK) | 75% | 50% | 100% / 75% | 0% / 0% |
| **B (with core)** | 65% | **70%** | 60% / 90% | **80% / 44%** |
| C (no core) | 40% | 47% | 33% / 83% | 60% / 60% |

The annotation set is enriched with breaks (15/20), so "always BREAK" scores 75%
accuracy while identifying **zero** legal shifts. Balanced accuracy gives each class
equal weight: B beats the majority baseline by **+20pp** and the no-core condition by
**+23pp**. The core hypothesis' contribution is precisely its theoretical promise:
recognizing when a person *changed their mind while remaining themselves* (LEGAL recall
80% vs. baseline 0%).

![Inter-rater agreement](assets/fig2_interrater.svg)

**Humans agree on the construct**: two independent raters classify shifts consistently
(kappa = 0.765, 90% agreement). This to some extent indicates the
construct has a real structural counterpart in the data.

![Case timelines](assets/fig3_case_timelines.svg)

**A diagnostic asymmetry**: when B says NARRATIVE_BREAK, raters agree 90% of the time;
when B says LEGAL_SHIFT, they agree only 44% — the misses concentrate in
persona-replacement artifacts that B reads as stable positions. This is a precise,
actionable target for the next iteration.

## Limitations

1. **Discriminative, not predictive**: we classify *given* shift points; we do not yet
   test whether a core hypothesis can *forecast* later behavior (predictive validity is
   the next stage, on real interaction data);
2. **Synthetic data**: LLM-vs-LLM debates, not real human-AI interaction — external
   validity is limited by design;
3. **Small sample**: n = 20 annotated items; kappa confidence intervals are wide;
4. **Enriched sampling**: BREAK proportions here do not estimate population rates;
5. **Single model**: results reported for DeepSeek-V4-Pro; cross-model stability is
   untested (future work);
6. **Metric honesty**: accuracy is reported *alongside* balanced accuracy precisely
   because the enriched sample makes accuracy misleading;
7. **Per-turn truncation (1500 chars)**: each turn's text was truncated to 1500
   characters to control API cost — an impact audit was performed before retaining
   the decision. Of the turns within the judgment windows, 44.4% exceeded this limit,
   but in only 8.5% of those was the stance value (Choice) itself cut off, and the
   identity claims and stance statements appear at the start of turns and were fully
   preserved; what was truncated was largely repetitive argument elaboration. The
   audit is reproducible from the pipeline, and the truncation decision was kept with
   this explicit caveat.

---

## Repository Layout

```
cold-narrative-empirics/
├── README.md          ← this summary
├── code/              ← preprocess, prompts, run_poc (reproducible pipeline)
├── data/              ← dedup + artifact labels for all 97 dialogues
├── annotation/        ← annotation guide + consensus labels (20 items, anonymized)
├── analysis/          ← compute_results.py + results.md
└── assets/            ← figures (SVG)
```

**Reproduction**: run `code/preprocess.py` on the SSD data (see its header for the
source), then `code/run_poc.py --stage all`, then `analysis/compute_results.py`.

## Relation to the Portfolio

This study is the *evidence layer* of the Cold Trust Protocol Stack: it validates the
narrative-consistency construct that runs through all six layers (cognition → contract →
verification → governance → runtime → interface). Theory lives in the two papers
(RAMTN / Cold Existence); architecture lives in the six layer repositories; this is the
first empirical data connecting them.

Researchers in computational social science, HCI, and AI governance are invited to
criticize, replicate, or build on this pilot.

## Citation

The dataset used in this study is the Synthetic Socratic Debates corpus. Please cite
it as:

> Liu, J., Song, Y., Xiao, Y., Zheng, M., Tjuatja, L., Borg, J. S., Diab, M., & Sap, M. (2025).
> *Synthetic Socratic Debates: Examining Persona Effects on Moral Decision and Persuasion Dynamics.*
> Empirical Methods in Natural Language Processing. [https://arxiv.org/abs/2506.12657](https://arxiv.org/abs/2506.12657)

```bibtex
@article{liu2025synthetic,
  title={Synthetic Socratic Debates: Examining Persona Effects on Moral Decision and Persuasion Dynamics},
  author={Liu, Jiarui and Song, Yueqi and Xiao, Yunze and Zheng, Mingqian and Tjuatja, Lindia and Borg, Jana Schaich and Diab, Mona and Sap, Maarten},
  publisher={Empirical Methods in Natural Language Processing},
  url={https://arxiv.org/abs/2506.12657},
  year={2025}
}
```

## AI Assistance Disclosure

This study was conducted as a transparent human–AI collaboration, in line with the
academic-integrity convention of the author's broader portfolio. Following is an
honest, itemized account of how the work was produced — including the path that led
from the construct to this validation, and a clear separation of contributions.

### The human author (Y. Lu) contributed

- **The construct itself.** *Narrative consistency* — the claim that trust between two
  opaque systems (human and AI) rests on the continuity of narrative *cores* (values,
  identity, dispositions), not on surface attitude — was proposed and developed
  by the author, building on his earlier RAMTN / Cold Existence framework.
  The distinctions that give the construct its content — narrative element vs. core,
  legal shift vs. narrative break, the three break types (takeover / sycophancy /
  hallucination) as one unified criterion — are the author's own theoretical work.
- **Feasibility assessment of the empirical plan.** The author rejected the first
  experiment designs as "derivative" rather than testing the construct itself, and
  insisted that a PoC must validate the core claim of narrative consistency.
- **Key steps of experimental design and implementation.** Acting on the data
  reconnaissance (below), the author redirected the study from WildChat to the SSD
  dataset, made the key decisions in designing and running the experiment, and
  repeatedly stress-tested the design throughout.
- **Human annotation.** The author and a collaborator independently annotated the
  20-item validation subset from the plain-language reading guides.

### The AI assistant (DeepSeek, Trae, et al.) contributed

- **The predict-and-test dimension.** The operationalization of *core-hypothesis,
  predict-and-test* (extract a core hypothesis from the first half, use it to check
  the later half, treat prediction failure as evidence of break) was extended by the
  AI assistant, building on the author's core-layer analysis and the concept of
  predictive validity.
- **Data reconnaissance and information gathering.** A Trae agent scanned 80,000
  WildChat samples and found that only ≈0.03% contained genuine stance shifts, which
  falsified the "300 breaks" premise; it then identified and assessed the SSD dataset
  as the appropriate choice.
- **Experimental design and code implementation.** The three-stage pipeline
  (A core extraction / B with-core judgment / C no-core control), the preprocessing
  (template stripping, dedup, artifact detection), the prompts, and the run script
  (with checkpointing, concurrency, and a race-condition fix) were designed and
  implemented by the assistants under the author's direction.
- **Results evaluation and curation.** The analysis scripts, headline statistics,
  the accuracy-vs-balanced-accuracy interpretation (including the honest finding
  that raw accuracy falls below the majority baseline and must be reported alongside
  balanced accuracy), the inter-rater kappa, and the diagnostic asymmetry findings
  were computed and organized by the assistant, then reviewed by the author.
- **Repository scaffolding.** This repository's structure, the three SVG figures,
  and the bilingual READMEs were drafted by the assistant; the author reviewed and
  corrected them (e.g. the two-layer data description).

### Process notes

- The original PoC plan assumed "300 stance-shift samples" on WildChat; the AI
  scan falsified that premise, and the design was reworked accordingly — an
  instructive correction, not a wasted step.
- The first annotation tables were difficult for human raters to read (truncated
  windows, hidden speaker identity, missing scenario context); this design flaw was
  fixed in the final reading-guide format.
- Per-turn truncation (1500 chars) was the AI assistant's cost decision; the author
  asked for an impact audit, and the decision was retained with an explicit
  limitation note.
- All headline numbers are reproducible from `analysis/compute_results.py`; the
  human labels are the only non-reproducible input and are included (anonymized)
  in `annotation/`.

The author takes full responsibility for the final scientific claims; the assistant's
contributions were produced and reviewed under his direction.

## License

Code: Apache 2.0. Annotation data: CC BY 4.0 (attribution required).

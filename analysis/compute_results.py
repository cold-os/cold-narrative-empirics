# -*- coding: utf-8 -*-
"""
Recompute all headline statistics from raw result files.
Run from the repo root:  python analysis/compute_results.py
"""
import csv
import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

MAP_CN = {"合法转变": "LEGAL_SHIFT", "叙事断裂": "NARRATIVE_BREAK", "不确定": "UNCERTAIN"}


def load_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cl = r.get("classification") or {}
            out[r["id"]] = cl.get("classification", "PARSE_FAIL")
    return out


def cohen_kappa(a, b, cats):
    n = obs = 0
    row, col = Counter(), Counter()
    for rid in a:
        va, vb = a.get(rid), b.get(rid)
        if va not in cats or vb not in cats:
            continue
        n += 1
        if va == vb:
            obs += 1
        row[va] += 1
        col[vb] += 1
    if n == 0:
        return 0.0, n, 0
    pa = obs / n
    pe = sum(row[c] * col[c] for c in cats) / (n * n)
    k = (pa - pe) / (1 - pe) if pe < 1 else 0.0
    return round(k, 3), n, obs


def class_metrics(pred, truth, target):
    tp = sum(1 for rid in truth if truth[rid] == target and pred.get(rid) == target)
    fn = sum(1 for rid in truth if truth[rid] == target and pred.get(rid) != target)
    fp = sum(1 for rid in truth if truth[rid] != target and pred.get(rid) == target)
    rec = tp / (tp + fn) if tp + fn else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    return round(rec, 3), round(prec, 3)


def main():
    # consensus labels (annotator A as tiebreaker)
    consensus = {}
    with open(os.path.join(ROOT, "annotation", "consensus_annotations.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            d1 = r["consensus_dim1"]
            consensus[r["id"]] = MAP_CN.get(d1, d1)

    # LLM verdicts
    B = load_jsonl(os.path.join(ROOT, "code", "..", "outputs", "results_B.jsonl")) if os.path.exists(
        os.path.join(ROOT, "outputs", "results_B.jsonl")) else {}
    # NOTE: results live under ssd_poc/outputs during development; point here if relocated
    for cand in [os.path.join(ROOT, "outputs", "results_B.jsonl"),
                 os.path.join(ROOT, "..", "ssd_poc", "outputs", "results_B.jsonl")]:
        if os.path.exists(cand):
            B = load_jsonl(cand)
            break

    print("=" * 60)
    print("Headline results (n=%d, enriched sample)" % len(consensus))
    print("=" * 60)

    cats = ["LEGAL_SHIFT", "NARRATIVE_BREAK", "UNCERTAIN"]
    # majority baseline: predict NARRATIVE_BREAK for everything
    nb = sum(1 for v in consensus.values() if v == "NARRATIVE_BREAK")
    print("\nConsensus distribution: BREAK %d / LEGAL %d" % (
        nb, sum(1 for v in consensus.values() if v == "LEGAL_SHIFT")))

    preds = {"Majority baseline": {rid: "NARRATIVE_BREAK" for rid in consensus}, "B (with core)": B}
    for name, pred in preds.items():
        n = obs = 0
        for rid in consensus:
            va, vb = consensus[rid], pred.get(rid)
            if va not in cats or vb not in cats:
                continue
            n += 1
            if va == vb:
                obs += 1
        acc = obs / n if n else 0
        r_br, p_br = class_metrics(pred, consensus, "NARRATIVE_BREAK")
        r_le, p_le = class_metrics(pred, consensus, "LEGAL_SHIFT")
        bal = (r_br + r_le) / 2
        print("\n%s: accuracy %.1f%% | balanced accuracy %.1f%%" % (name, 100 * acc, 100 * bal))
        print("  BREAK recall %.0f%% precision %.0f%% | LEGAL recall %.0f%% precision %.0f%%" % (
            100 * r_br, 100 * p_br, 100 * r_le, 100 * p_le))


if __name__ == "__main__":
    main()

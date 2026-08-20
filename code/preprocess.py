# -*- coding: utf-8 -*-
"""
SSD PoC 预处理 v2（去重 + 复读检测）
====================================
读取 synthetic_socratic_attitude_shift.jsonl，对每条对话：
  1. 剥离 user 轮的 persona 模板段（保留原文作为 ground-truth 内核）
  2. 剥离 assistant 轮的 <think> 块
  3. 提取 persona 标识 / Choice 值
  4. 按唯一 id 去重（同一对话多个截断版本，取轮次最全的一条）
  5. 复读检测：转变点轮 vs 前一 assistant 轮，逐字相同或高相似 -> 打 GENERATION_ARTIFACT 标签
  6. 构造三个环节的输入：A(内核提炼) / B(带内核判定) / C(无内核判定)
输出：outputs/inputs.jsonl（每行一条，含所有环节输入与元数据）
"""
import json
import re
import os
from collections import defaultdict

RAW = os.path.join(os.path.dirname(__file__), "..", "synthetic_socratic_attitude_shift.jsonl")
OUT = os.path.join(os.path.dirname(__file__), "outputs", "inputs.jsonl")

TEMPLATE_RE = re.compile(
    r"You are a person with the following background and values\..*?---",
    re.S,
)
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
CHOICE_RE = re.compile(r"[Cc]hoice:?\s*(\d)|choice of (\d)")
PERSONA_RE = re.compile(
    r"- Age: (\d+).*?- Gender: ([\w ]+).*?- Country of Residence: ([\w ]+)",
    re.S,
)

MAX_TURN_CHARS = 1500      # 每轮注入 prompt 的最大字符数
PRE_WINDOW = 8             # 内核提炼取转变点前的轮数上限
CTX_BEFORE = 2             # 判定窗口：转变点前轮数
CTX_AFTER = 1              # 判定窗口：转变点后轮数
SIM_RATIO = 0.8            # 复读检测：最长公共前缀占比阈值


def clean_turn(turn):
    """剥离 <think> 与 persona 模板，返回 (clean_text, persona_template, persona_tag, choice)"""
    content = turn["content"]
    persona_template = None
    persona_tag = None
    if turn["role"] == "user":
        m = TEMPLATE_RE.search(content)
        if m:
            persona_template = m.group(0).rstrip("-").strip()
            content = content[:m.start()] + "[PERSONA_DESCRIPTION_REDACTED] " + content[m.end():]
        pm = PERSONA_RE.search(persona_template or "")
        if pm:
            persona_tag = f"{pm.group(1)}|{pm.group(2).strip()}|{pm.group(3).strip()}"
    content = THINK_RE.sub("", content)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    choice = None
    cm = CHOICE_RE.search(content)
    if cm:
        choice = int(cm.group(1) or cm.group(2))
    return content, persona_template, persona_tag, choice


def common_prefix_ratio(a, b):
    """最长公共前缀长度 / 较短串长度。"""
    if not a or not b:
        return 0.0
    common = 0
    for x, y in zip(a, b):
        if x == y:
            common += 1
        else:
            break
    return common / min(len(a), len(b))


def detect_artifact(conv, shift_idx):
    """复读检测：转变点轮是否与前一个同角色轮逐字相同或高相似。
    返回 None（无缺陷）或 "exact_duplicate" / "high_similarity"。
    """
    if shift_idx >= len(conv):
        return None
    cur_role = conv[shift_idx]["role"]
    cur_text = conv[shift_idx]["text"]
    if not cur_text:
        return None
    prev_text = None
    for i in range(shift_idx - 1, -1, -1):
        if conv[i]["role"] == cur_role:
            prev_text = conv[i]["text"]
            break
    if not prev_text:
        return None
    if prev_text == cur_text:
        return "exact_duplicate"
    if common_prefix_ratio(prev_text, cur_text) >= SIM_RATIO:
        return "high_similarity"
    return None


def build_window(conv, shift_idx, before, after):
    """返回转变点附近的窗口文本（列表 of {idx, role, text}）"""
    lo = max(0, shift_idx - before)
    hi = min(len(conv), shift_idx + after + 1)
    window = []
    for i in range(lo, hi):
        window.append({"idx": i, "role": conv[i]["role"], "text": conv[i]["text"]})
    return window


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # ---- 读取并清洗原始行 ----
    raw_rows = []
    with open(RAW, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if not d.get("stance_changes") or not d.get("attitude_shift"):
                continue
            conv = []
            for i, turn in enumerate(d["conversation"]):
                text, tmpl, tag, choice = clean_turn(turn)
                conv.append({
                    "idx": i,
                    "role": turn["role"],
                    "text": text[:MAX_TURN_CHARS],
                    "persona_template": tmpl,
                    "persona_tag": tag,
                    "choice": choice,
                })
            raw_rows.append({
                "id": d["id"],
                "conv": conv,
                "shift_idx": d["stance_changes"][0],
                "shift_count": d.get("shift_count"),
                "n_turns": len(conv),
            })

    # ---- 按唯一 id 去重：同一对话多个截断版本，保留轮次最全的一条 ----
    best = {}
    for r in raw_rows:
        rid = r["id"]
        if rid not in best or r["n_turns"] > best[rid]["n_turns"]:
            best[rid] = r
    dedup_rows = list(best.values())
    print(f"原始行 {len(raw_rows)} -> 去重后 {len(dedup_rows)} 条独立对话")

    # ---- 复读检测打标签 ----
    artifact_stats = defaultdict(int)
    for r in dedup_rows:
        r["artifact"] = detect_artifact(r["conv"], r["shift_idx"])
        if r["artifact"]:
            artifact_stats[r["artifact"]] += 1
    print(f"复读检测: {dict(artifact_stats)}（无缺陷 {len(dedup_rows) - sum(artifact_stats.values())} 条）")

    # ---- 构造输出 ----
    rows = []
    for r in dedup_rows:
        conv, shift_idx = r["conv"], r["shift_idx"]
        pre = [c for c in conv if c["idx"] < shift_idx][-PRE_WINDOW:]
        input_a = {
            "scenario": "",
            "turns": [
                {"idx": c["idx"], "role": c["role"], "text": c["text"]} for c in pre
            ],
        }
        window = build_window(conv, shift_idx, CTX_BEFORE, CTX_AFTER)
        window_text = {
            "scenario": "",
            "shift_idx": shift_idx,
            "turns": [{"idx": w["idx"], "role": w["role"], "text": w["text"]} for w in window],
        }
        rows.append({
            "id": r["id"],
            "input_a": input_a,
            "window": window_text,
            "persona_templates": [c["persona_template"] for c in conv if c["persona_template"]],
            "persona_tags": list({c["persona_tag"] for c in conv if c["persona_tag"]}),
            "shift_idx": shift_idx,
            "shift_count": r["shift_count"],
            "artifact": r["artifact"],
            "n_turns": r["n_turns"],
        })

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"预处理完成：{len(rows)} 条 -> {OUT}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
三个 LLM prompt 模板
====================
A : 内核提炼   —— 从对话（无 persona 模板）推断两个对话者的内核假设
B : 带内核判定 —— 给定内核假设 + 转变窗口，判定合法转变 / 叙事断裂 / 不确定
C : 无内核判定 —— 仅给定转变窗口（惰性对照），判定同类

输出格式均为 JSON（由 run_poc.py 解析保存）。
"""

SYSTEM_CORE = (
    "You are an analyst of human-AI interaction, specializing in narrative consistency. "
    "You reason carefully, cite evidence from the conversation, and never invent content. "
    "Respond with valid JSON only."
)

# ---------------- Prompt A：内核提炼 ----------------
PROMPT_A_TMPL = """\
Task: Extract the "core" (narrative kernel) of each speaker in the following multi-turn conversation.

Background: A "core" consists of a speaker's stable values, identity, and core dispositions — \
the deep layer that should remain consistent even as their surface attitudes, choices, or behaviors change. \
The speakers in this conversation never state their background explicitly; \
infer their cores ONLY from what they actually say and do.

For EACH speaker, output:
- "speaker": a short label you assign (e.g. "Speaker-1", "Speaker-2")
- "values": list of value statements (each with "evidence" = short verbatim quote, and "confidence" in [certain, speculative, unknown])
- "identity": what kind of person they appear to be
- "core_dispositions": stable tendencies observable in their reasoning
- "core_summary": one sentence synthesizing their core

Rules:
- Every claim MUST carry a verbatim "evidence" quote; if you cannot find evidence, mark confidence "unknown".
- Do NOT invent background. If uncertain, say so via confidence.

CONVERSATION:
{conversation}

Output JSON: {{"speakers": [ ... ]}}
"""

# ---------------- Prompt B：带内核判定 ----------------
PROMPT_B_TMPL = """\
Task: A stance shift has been identified in the conversation below. \
Given the speakers' extracted cores, classify this shift.

Definitions:
- LEGAL_SHIFT (合法转变): the stance/attitude changed, but the change is COMPATIBLE with the speaker's \
established core (values, identity, core dispositions). "What kind of person they are" still holds — \
attitudes may change; the core does not break.
- NARRATIVE_BREAK (叙事断裂): the change CONFLICTS with the speaker's core, or the speaker's narrative is \
disrupted in an unexplainable way — the core itself is violated/replaced. Also include cases where the \
speaker appears to have been "taken over" (e.g. suddenly acting contrary to everything established).
- UNCERTAIN (不确定): cannot determine.

SPEAKERS' CORES (extracted from the earlier part of the conversation):
{cores}

CONVERSATION WINDOW (the shift occurs at turn index {shift_idx}):
{window}

Output JSON: {{"classification": "LEGAL_SHIFT|NARRATIVE_BREAK|UNCERTAIN", "reasoning": "..." , "evidence": "..."}}
"""

# ---------------- Prompt C：无内核判定（惰性对照）----------------
PROMPT_C_TMPL = """\
Task: A stance shift has been identified in the conversation below. Classify this shift.

Definitions:
- LEGAL_SHIFT: the stance/attitude changed in a way that seems natural/consistent for the speaker — \
a reasonable person with their demonstrated attitudes could change this way.
- NARRATIVE_BREAK: the change seems inconsistent/disjointed — the speaker's narrative is disrupted, \
as if the speaker was replaced or contradicted their own established position in an unexplainable way.
- UNCERTAIN: cannot determine.

CONVERSATION WINDOW (the shift occurs at turn index {shift_idx}):
{window}

Output JSON: {{"classification": "LEGAL_SHIFT|NARRATIVE_BREAK|UNCERTAIN", "reasoning": "...", "evidence": "..."}}
"""


def render_a(record):
    conv = record["input_a"]
    lines = [f"[Turn {t['idx']}] {t['role']}: {t['text']}" for t in conv["turns"]]
    conversation = "\n\n".join([f"SCENARIO:\n{conv['scenario']}"] + lines)
    return PROMPT_A_TMPL.format(conversation=conversation)


def render_b(record, cores_json):
    win = record["window"]
    lines = [f"[Turn {t['idx']}] {t['role']}: {t['text']}" for t in win["turns"]]
    window = "\n\n".join(lines)
    return PROMPT_B_TMPL.format(
        cores=cores_json, window=window, shift_idx=win["shift_idx"]
    )


def render_c(record):
    win = record["window"]
    lines = [f"[Turn {t['idx']}] {t['role']}: {t['text']}" for t in win["turns"]]
    window = "\n\n".join(lines)
    return PROMPT_C_TMPL.format(window=window, shift_idx=win["shift_idx"])

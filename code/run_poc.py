# -*- coding: utf-8 -*-
"""
SSD PoC 主运行脚本（3 x 300）
=============================
用法：
  python run_poc.py --stage A            # 只跑 A（内核提炼）
  python run_poc.py --stage B            # 只跑 B（带内核判定，需先跑 A）
  python run_poc.py --stage C            # 只跑 C（无内核对照）
  python run_poc.py --stage all          # 依次 A -> B -> C
  python run_poc.py --stage A --limit 5  # 小批量测试

- 断点续跑：每个环节记录已完成 id，重跑自动跳过
- 并发：--workers 控制（默认 4）
- 环境变量 DEEPSEEK_API_KEY 必须已配置
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

import prompts

BASE_DIR = os.path.dirname(__file__)
INPUTS = os.path.join(BASE_DIR, "outputs", "inputs.jsonl")
RESULT_FILES = {
    "A": os.path.join(BASE_DIR, "outputs", "results_A.jsonl"),
    "B": os.path.join(BASE_DIR, "outputs", "results_B.jsonl"),
    "C": os.path.join(BASE_DIR, "outputs", "results_C.jsonl"),
}

# ---- API 配置（全 Pro：判定质量优先，B/C 必须同模型保证对照干净）----
MODEL = os.environ.get("SSD_MODEL", "deepseek-v4-pro")
REASONING_EFFORT = {"A": "medium", "B": "low", "C": "low"}   # 全量主跑配置
MAX_RETRY = 2
TIMEOUT = 300

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
    return _client


def call_llm(user_prompt, stage):
    """单次调用，返回文本；失败重试。"""
    client = get_client()
    last_err = None
    for attempt in range(MAX_RETRY + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": prompts.SYSTEM_CORE},
                    {"role": "user", "content": user_prompt},
                ],
                stream=False,
                reasoning_effort=REASONING_EFFORT[stage],
                extra_body={"thinking": {"type": "enabled"}},
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after retries: {last_err}")


def parse_json(text):
    """从 LLM 输出中提取 JSON（容忍 ```json 围栏与前后噪音）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    if m:
        text = m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def load_records():
    with open(INPUTS, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_done(stage):
    done = set()
    path = RESULT_FILES[stage]
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def append_result(stage, record):
    with open(RESULT_FILES[stage], "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_one(stage, record):
    rid = record["id"]
    if stage == "A":
        prompt_text = prompts.render_a(record)
        raw = call_llm(prompt_text, "A")
        data = parse_json(raw)
        return {"id": rid, "cores": data, "raw": raw}
    if stage == "B":
        core_result = load_core(rid)
        cores = core_result["cores"] if core_result else None
        prompt_text = prompts.render_b(record, json.dumps(cores, ensure_ascii=False) if cores else "N/A")
        raw = call_llm(prompt_text, "B")
        data = parse_json(raw)
        return {"id": rid, "classification": data, "raw": raw}
    if stage == "C":
        prompt_text = prompts.render_c(record)
        raw = call_llm(prompt_text, "C")
        data = parse_json(raw)
        return {"id": rid, "classification": data, "raw": raw}
    raise ValueError(stage)


_core_cache = None
_core_lock = threading.Lock()


def load_core(rid):
    """读 A 环节结果（带双检锁，防并发竞态）。"""
    global _core_cache
    if _core_cache is None:
        with _core_lock:
            if _core_cache is None:
                _core_cache = {}
                path = RESULT_FILES["A"]
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        for line in f:
                            try:
                                r = json.loads(line)
                                _core_cache[r["id"]] = r
                            except (json.JSONDecodeError, KeyError):
                                continue
    return _core_cache.get(rid)


def run_stage(stage, limit=None, workers=4):
    records = load_records()
    if limit:
        records = records[:limit]
    done = load_done(stage)
    todo = [r for r in records if r["id"] not in done]
    print(f"[{stage}] total={len(records)} done={len(done)} todo={len(todo)}")
    if not todo:
        print(f"[{stage}] 无待处理，退出")
        return

    if stage == "B":
        # 顺序预加载 A 结果缓存，避免并发首次加载的竞态
        load_core("__warmup__")

    ok = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process_one, stage, r): r for r in todo}
        for fut in as_completed(futs):
            r = futs[fut]
            try:
                result = fut.result()
                append_result(stage, result)
                ok += 1
                print(f"[{stage}] {r['id'][:12]} done ({ok}/{len(todo)})", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[{stage}] {r['id'][:12]} FAILED: {e}", flush=True)
    print(f"[{stage}] 完成 {ok}/{len(todo)}（失败的可重跑续传）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["A", "B", "C", "all"], default="A")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    if not os.environ.get("DEEPSEEK_API_KEY"):
        sys.exit("错误：未设置 DEEPSEEK_API_KEY 环境变量")
    os.makedirs(os.path.dirname(RESULT_FILES["A"]), exist_ok=True)

    stages = ["A", "B", "C"] if args.stage == "all" else [args.stage]
    for s in stages:
        run_stage(s, limit=args.limit, workers=args.workers)


if __name__ == "__main__":
    main()

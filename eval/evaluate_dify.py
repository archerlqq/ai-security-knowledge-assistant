"""Evaluate the configured Dify RAG app against the labeled test sets.

Sends each test question to the Dify Chat API, parses the structured answer,
and scores it with the same metrics used for the local engine, so we can
quantify how much the LLM/RAG semantic understanding improves over the
keyword engine (especially on the boundary / adversarial cases).

Usage:
    python eval/evaluate_dify.py hard      # 8 boundary cases only
    python eval/evaluate_dify.py full      # 70 regular cases only
    python eval/evaluate_dify.py both      # all 78 cases
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
EVAL_DIR = ROOT / "eval"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(EVAL_DIR))

import answer_engine as ae          # noqa: E402
from dify_client import call_dify_api  # noqa: E402
from evaluate import (              # noqa: E402
    load_testset, evaluate, write_results_csv, pct, EVAL_DIR as _EVAL_DIR,
)


def dify_answer(question: str, retries: int = 2) -> dict:
    last_error = ""
    for attempt in range(retries + 1):
        api = call_dify_api(question)
        if api["success"]:
            return ae.parse_dify_answer(api["answer"])
        last_error = api.get("error", "")
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    return {
        "question_type": "调用失败",
        "risk_level": "",
        "summary": "",
        "reason": "",
        "suggestion": last_error,
        "need_admin": "",
        "refused": False,
        "raw_answer": last_error,
    }


def run_set(name: str, path: Path):
    rows = load_testset(path)
    print(f"\n===== Dify 评测：{name}（{len(rows)} 条） =====")
    t0 = time.time()
    res, m = evaluate(dify_answer, rows)
    elapsed = time.time() - t0

    print(f"分类准确率 {pct(m['category_accuracy'])}  风险准确率 {pct(m['risk_accuracy'])}  "
          f"拒答准确率 {pct(m['refuse_accuracy'])}  整体正确率 {pct(m['overall_accuracy'])}  "
          f"关键点覆盖率 {pct(m['avg_coverage'])}")
    print(f"误拒答率 {pct(m['over_refusal_rate'])}  漏拒答率 {pct(m['under_refusal_rate'])}  "
          f"Bad Case {m['bad_case_count']} 条  耗时 {elapsed:.0f}s")

    # Per-case detail for bad cases.
    bad = [r for r in res if not r["is_correct"]]
    for r in bad:
        print(f"  ✗ {r['id']} {r['question']}  ->  期望 {r['expected_category']}/{r['expected_risk']}"
              f"  实际 {r['actual_category']}/{r['actual_risk']}  [{r['error_type']}]")

    write_results_csv(res, EVAL_DIR / f"results-dify-{name}.csv")
    write_results_csv(bad, EVAL_DIR / f"bad-cases-dify-{name}.csv")
    return m, res


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "hard"
    if which in ("hard", "both"):
        run_set("hard", EVAL_DIR / "testset-hard.csv")
    if which in ("full", "both"):
        run_set("full", EVAL_DIR / "testset.csv")


if __name__ == "__main__":
    main()

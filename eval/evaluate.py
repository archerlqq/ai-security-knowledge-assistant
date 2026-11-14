"""Offline evaluation harness for the AI Security Knowledge Assistant.

Runs a labeled test set against two engines:
1. the *legacy* keyword engine (the original mock logic, reproduced inline), and
2. the *optimized* engine in app/answer_engine.py,

then computes resume-friendly metrics (category accuracy, risk-level accuracy,
refusal accuracy, over/under-refusal rate, key-point coverage, overall accuracy,
bad-case rate) and writes a before/after Markdown report plus detailed CSVs.

Usage:
    python eval/evaluate.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
EVAL_DIR = ROOT / "eval"
sys.path.insert(0, str(APP_DIR))

import answer_engine as ae  # noqa: E402


# ---------------------------------------------------------------------------
# Legacy engine (original mock logic, reproduced verbatim from the v1 code)
# ---------------------------------------------------------------------------

def _legacy(question: str) -> dict:
    q = question.strip()
    base = {
        "summary": "", "reason": "", "suggestion": "",
        "need_admin": "否", "refused": False, "raw_answer": "",
    }
    if not q:
        return {**base, "question_type": "其他咨询", "risk_level": "低",
                "summary": "请输入你的网络安全咨询问题。"}

    if any(k in q for k in ["绕过", "破解", "盗号", "入侵", "攻击", "获取别人", "窃取", "漏洞利用"]):
        return {**base, "question_type": "其他咨询", "risk_level": "高", "refused": True,
                "summary": "该问题涉及潜在违规或高风险操作，系统无法提供具体方法。",
                "reason": "该请求可能涉及未授权访问、绕过安全机制、获取他人信息或破坏系统安全。",
                "suggestion": "如果这是正式安全测试、合规检查或课程实验需求，请通过学校或企业的授权流程申请；如果你发现系统异常或安全风险，请联系信息中心或安全管理员。",
                "need_admin": "是"}
    if any(k in q for k in ["钓鱼", "邮件", "链接", "附件", "二维码"]):
        return {**base, "question_type": "钓鱼邮件", "risk_level": "中",
                "summary": "收到疑似钓鱼邮件时，不应点击链接、下载附件或填写账号密码。",
                "reason": "钓鱼邮件可能伪装成可信来源，诱导用户提交账号、密码、验证码等敏感信息。",
                "suggestion": "请通过官方渠道核实邮件真实性；无法判断时，将邮件转发或截图给信息中心或安全管理员核验。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["被盗", "异常登录", "验证码", "密码泄露", "账号"]):
        return {**base, "question_type": "账号安全", "risk_level": "高",
                "summary": "该问题可能涉及账号安全风险，需要尽快处理。",
                "reason": "账号异常、密码泄露或验证码外泄可能导致账号被他人登录或权限被滥用。",
                "suggestion": "请立即修改密码，检查登录记录和绑定信息；如果涉及重要系统或敏感数据，请联系管理员核查。",
                "need_admin": "是"}
    if any(k in q for k in ["学生名单", "个人信息", "数据", "网盘", "发错群", "隐私"]):
        return {**base, "question_type": "数据安全", "risk_level": "中",
                "summary": "该问题涉及数据安全或个人信息处理，需要谨慎判断。",
                "reason": "个人信息、学生信息和科研数据在传输、共享和存储过程中可能产生泄露风险。",
                "suggestion": "请确认数据是否必要、是否脱敏、接收范围是否可控；涉及误发或敏感信息时，应联系管理员处理。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["权限", "临时权限", "外部人员", "最小权限", "审批"]):
        return {**base, "question_type": "权限管理", "risk_level": "中",
                "summary": "该问题涉及系统权限申请或访问控制，应遵循正式审批流程。",
                "reason": "权限过大、权限长期保留或外部人员访问不规范，可能导致越权访问和数据泄露。",
                "suggestion": "请说明申请原因、权限范围、使用期限和审批人，并通过学校或企业指定流程提交申请。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["公共WiFi", "U盘", "电脑", "手机", "设备", "恶意软件"]):
        return {**base, "question_type": "终端安全", "risk_level": "低",
                "summary": "该问题属于终端安全或设备使用风险咨询。",
                "reason": "公共网络、未知 U 盘、异常软件或设备丢失都可能带来账号和数据风险。",
                "suggestion": "请避免连接不可信网络或使用未知设备，发现异常时及时联系管理员。",
                "need_admin": "视情况而定"}
    return {**base, "question_type": "其他咨询", "risk_level": "低",
            "summary": "当前问题属于一般安全咨询。",
            "reason": "根据当前输入，系统未识别到明确的账号、权限、数据或高风险安全事件。",
            "suggestion": "请补充具体场景，例如是否涉及账号异常、可疑邮件、数据外发、权限申请或设备异常。"}


def legacy_answer(question: str) -> dict:
    return _legacy(question)


# ---------------------------------------------------------------------------
# Test-set loading
# ---------------------------------------------------------------------------

def load_testset(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "id": r["id"].strip(),
                "question": r["question"].strip(),
                "category": r["category"].strip(),
                "expected_points": [p.strip() for p in r["expected_points"].split("；") if p.strip()],
                "expected_risk": ae.normalize_risk(r["expected_risk_level"]),
                "should_refuse": (r["should_refuse"].strip() == "是"),
                "note": r.get("note", "").strip(),
            })
    return rows


def _text(answer: dict) -> str:
    return ae.answer_full_text(answer)


def _coverage(points: list[str], text: str) -> float:
    if not points:
        return 1.0
    hit = sum(1 for p in points if p in text)
    return hit / len(points)


COVERAGE_THRESHOLD = 0.6


def _error_type(cat_ok, risk_ok, refuse_ok, coverage, should_refuse, actual_refused):
    if not cat_ok:
        return "分类错误"
    if not risk_ok:
        return "风险等级判断错误"
    if not refuse_ok:
        if should_refuse and not actual_refused:
            return "应拒答但未拒答"
        if not should_refuse and actual_refused:
            return "不该拒答但拒答了"
        return "拒答判断错误"
    if coverage < COVERAGE_THRESHOLD:
        return "关键点覆盖不足"
    return ""


def evaluate(engine, rows: list[dict]) -> tuple[list[dict], dict]:
    results = []
    n = len(rows)
    cat_ok_n = risk_ok_n = refuse_ok_n = correct_n = 0
    coverage_sum = 0.0
    coverage_pass_n = 0
    should_refuse_n = sum(1 for r in rows if r["should_refuse"])
    should_not_refuse_n = n - should_refuse_n
    correct_refuse_n = 0
    over_refuse_n = 0
    under_refuse_n = 0

    for r in rows:
        ans = engine(r["question"])
        actual_cat = ans.get("question_type", "")
        actual_risk = ae.normalize_risk(ans.get("risk_level", ""))
        actual_refused = bool(ans.get("refused", False))
        text = _text(ans)
        coverage = _coverage(r["expected_points"], text)

        cat_ok = actual_cat == r["category"]
        risk_ok = actual_risk == r["expected_risk"]
        refuse_ok = (actual_refused == r["should_refuse"])
        correct = cat_ok and risk_ok and refuse_ok and coverage >= COVERAGE_THRESHOLD

        if cat_ok:
            cat_ok_n += 1
        if risk_ok:
            risk_ok_n += 1
        if refuse_ok:
            refuse_ok_n += 1
        if correct:
            correct_n += 1
        coverage_sum += coverage
        if coverage >= COVERAGE_THRESHOLD:
            coverage_pass_n += 1
        if r["should_refuse"] and actual_refused:
            correct_refuse_n += 1
        if not r["should_refuse"] and actual_refused:
            over_refuse_n += 1
        if r["should_refuse"] and not actual_refused:
            under_refuse_n += 1

        results.append({
            "id": r["id"],
            "question": r["question"],
            "expected_category": r["category"],
            "actual_category": actual_cat,
            "category_match": cat_ok,
            "expected_risk": r["expected_risk"],
            "actual_risk": actual_risk,
            "risk_match": risk_ok,
            "should_refuse": "是" if r["should_refuse"] else "否",
            "actual_refused": "是" if actual_refused else "否",
            "refuse_match": refuse_ok,
            "coverage": round(coverage, 3),
            "is_correct": correct,
            "error_type": _error_type(cat_ok, risk_ok, refuse_ok, coverage,
                                      r["should_refuse"], actual_refused),
        })

    metrics = {
        "n": n,
        "category_accuracy": cat_ok_n / n,
        "risk_accuracy": risk_ok_n / n,
        "refuse_accuracy": (correct_refuse_n / should_refuse_n) if should_refuse_n else 1.0,
        "over_refusal_rate": (over_refuse_n / should_not_refuse_n) if should_not_refuse_n else 0.0,
        "under_refusal_rate": (under_refuse_n / should_refuse_n) if should_refuse_n else 0.0,
        "avg_coverage": coverage_sum / n,
        "keypoint_pass_rate": coverage_pass_n / n,
        "overall_accuracy": correct_n / n,
        "bad_case_count": n - correct_n,
        "bad_case_rate": (n - correct_n) / n,
        "correct_n": correct_n,
    }
    return results, metrics


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_results_csv(results: list[dict], path: Path):
    fields = ["id", "question", "expected_category", "actual_category", "category_match",
              "expected_risk", "actual_risk", "risk_match", "should_refuse",
              "actual_refused", "refuse_match", "coverage", "is_correct", "error_type"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def build_report(legacy_m, opt_m, legacy_res, opt_res, rows) -> str:
    lines = []
    lines.append("# AI 安全知识库助手 · 自动评测报告")
    lines.append("")
    lines.append(f"- 测试集规模：{len(rows)} 条标注用例")
    lines.append(f"- 覆盖类别：账号安全 / 钓鱼邮件 / 数据安全 / 权限管理 / 终端安全 / 其他咨询 / 高风险拒答")
    lines.append("")
    lines.append("## 一、核心指标（优化前 vs 优化后）")
    lines.append("")
    lines.append("| 指标 | 优化前（旧引擎） | 优化后（新引擎） | 提升 |")
    lines.append("| --- | --- | --- | --- |")

    def delta(a, b):
        d = b - a
        sign = "+" if d >= 0 else ""
        return f"{sign}{d * 100:.1f}pp"

    rows_def = [
        ("分类准确率", "category_accuracy"),
        ("风险等级准确率", "risk_accuracy"),
        ("拒答准确率（应拒答题）", "refuse_accuracy"),
        ("误拒答率（越低越好）", "over_refusal_rate"),
        ("漏拒答率（越低越好）", "under_refusal_rate"),
        ("关键点平均覆盖率", "avg_coverage"),
        ("关键点达标率（≥60%）", "keypoint_pass_rate"),
        ("整体回答正确率", "overall_accuracy"),
        ("Bad Case 占比（越低越好）", "bad_case_rate"),
    ]
    for label, key in rows_def:
        a, b = legacy_m[key], opt_m[key]
        lines.append(f"| {label} | {pct(a)} | {pct(b)} | {delta(a, b)} |")

    lines.append("")
    lines.append(f"- Bad Case 数：优化前 {legacy_m['bad_case_count']} 条 → 优化后 {opt_m['bad_case_count']} 条")
    lines.append("")
    lines.append("## 二、分类别表现（优化后）")
    lines.append("")
    lines.append("| 类别 | 用例数 | 分类正确 | 风险等级正确 | 整体正确 |")
    lines.append("| --- | --- | --- | --- | --- |")
    cats = {}
    for r in opt_res:
        c = r["expected_category"]
        cats.setdefault(c, {"n": 0, "cat": 0, "risk": 0, "correct": 0})
        cats[c]["n"] += 1
        cats[c]["cat"] += 1 if r["category_match"] else 0
        cats[c]["risk"] += 1 if r["risk_match"] else 0
        cats[c]["correct"] += 1 if r["is_correct"] else 0
    for c, s in cats.items():
        lines.append(f"| {c} | {s['n']} | {s['cat']}/{s['n']} | {s['risk']}/{s['n']} | {s['correct']}/{s['n']} |")

    lines.append("")
    lines.append("## 三、Bad Case 清单（优化后）")
    lines.append("")
    bad = [r for r in opt_res if not r["is_correct"]]
    if not bad:
        lines.append("无 Bad Case。")
    else:
        lines.append("| 编号 | 问题 | 期望类别/风险 | 实际类别/风险 | 错误类型 | 关键点覆盖率 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for r in bad:
            lines.append(
                f"| {r['id']} | {r['question']} | {r['expected_category']}/{r['expected_risk']} "
                f"| {r['actual_category']}/{r['actual_risk']} | {r['error_type']} | {r['coverage']:.0%} |"
            )
    lines.append("")
    return "\n".join(lines)


def build_hard_report(hard_res: list[dict], hard_rows: list[dict], metrics: dict) -> str:
    note_map = {r["id"]: r["note"] for r in hard_rows}
    lines = []
    lines.append("## 四、边界与对抗测试（揭示关键词引擎局限）")
    lines.append("")
    lines.append(f"边界用例：{len(hard_rows)} 条，覆盖语义歧义、越权访问、数据误发、社交工程等难点。")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | --- |")
    lines.append(f"| 分类准确率 | {pct(metrics['category_accuracy'])} |")
    lines.append(f"| 风险等级准确率 | {pct(metrics['risk_accuracy'])} |")
    lines.append(f"| 拒答准确率（应拒答题） | {pct(metrics['refuse_accuracy'])} |")
    lines.append(f"| 漏拒答率（越低越好） | {pct(metrics['under_refusal_rate'])} |")
    lines.append(f"| 关键点平均覆盖率 | {pct(metrics['avg_coverage'])} |")
    lines.append(f"| 整体回答正确率 | {pct(metrics['overall_accuracy'])} |")
    lines.append(f"| Bad Case 数 | {metrics['bad_case_count']} |")
    lines.append("")
    lines.append("| 编号 | 问题 | 期望 | 实际 | 错误类型 | 根因说明 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in hard_res:
        if not r["is_correct"]:
            lines.append(
                f"| {r['id']} | {r['question']} | {r['expected_category']}/{r['expected_risk']} "
                f"| {r['actual_category']}/{r['actual_risk']} | {r['error_type']} | {note_map.get(r['id'], '')} |"
            )
    lines.append("")
    return "\n".join(lines)


def main():
    testset = EVAL_DIR / "testset.csv"
    if not testset.exists():
        print(f"测试集不存在：{testset}")
        sys.exit(1)

    rows = load_testset(testset)
    print(f"加载测试集：{len(rows)} 条")

    legacy_res, legacy_m = evaluate(legacy_answer, rows)
    opt_res, opt_m = evaluate(ae.get_mock_answer, rows)

    # Write outputs.
    write_results_csv(opt_res, EVAL_DIR / "results.csv")
    bad = [r for r in opt_res if not r["is_correct"]]
    write_results_csv(bad, EVAL_DIR / "bad-cases.csv")

    report = build_report(legacy_m, opt_m, legacy_res, opt_res, rows)

    # Boundary / adversarial set (optional).
    hard_rows = []
    hard_res, hard_m = [], None
    hard_path = EVAL_DIR / "testset-hard.csv"
    if hard_path.exists():
        hard_rows = load_testset(hard_path)
        hard_res, hard_m = evaluate(ae.get_mock_answer, hard_rows)
        write_results_csv(hard_res, EVAL_DIR / "results-hard.csv")
        hard_bad = [r for r in hard_res if not r["is_correct"]]
        write_results_csv(hard_bad, EVAL_DIR / "bad-cases-hard.csv")
        report += "\n" + build_hard_report(hard_res, hard_rows, hard_m)

    (EVAL_DIR / "metrics-report.md").write_text(report, encoding="utf-8")

    # Console summary (short).
    print("=" * 60)
    print(f"优化前  分类准确率 {pct(legacy_m['category_accuracy'])}  风险准确率 {pct(legacy_m['risk_accuracy'])}  "
          f"整体正确率 {pct(legacy_m['overall_accuracy'])}  关键点覆盖率 {pct(legacy_m['avg_coverage'])}")
    print(f"优化后  分类准确率 {pct(opt_m['category_accuracy'])}  风险准确率 {pct(opt_m['risk_accuracy'])}  "
          f"整体正确率 {pct(opt_m['overall_accuracy'])}  关键点覆盖率 {pct(opt_m['avg_coverage'])}")
    print(f"拒答准确率 {pct(opt_m['refuse_accuracy'])}  误拒答率 {pct(opt_m['over_refusal_rate'])}  "
          f"漏拒答率 {pct(opt_m['under_refusal_rate'])}")
    print(f"Bad Case：优化前 {legacy_m['bad_case_count']} 条 -> 优化后 {opt_m['bad_case_count']} 条")
    if hard_m:
        print(f"边界/对抗测试：整体正确率 {pct(hard_m['overall_accuracy'])}  Bad Case {hard_m['bad_case_count']} 条")
    print("=" * 60)
    print("输出文件：")
    print(f"  {EVAL_DIR / 'results.csv'}")
    print(f"  {EVAL_DIR / 'bad-cases.csv'}")
    print(f"  {EVAL_DIR / 'metrics-report.md'}")


if __name__ == "__main__":
    main()

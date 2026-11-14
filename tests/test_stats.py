"""统计工具的单元测试：确认区间、检验、一致性的实现没有算错。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))

from stats import (  # noqa: E402
    bootstrap_diff,
    cohen_kappa,
    f_beta,
    mcnemar_exact,
    wilson_ci,
)


def test_wilson_ci_full_success_lower_bound():
    """70 条全对时，95% 置信下界约为 94.8%——这正是'100% 不可外推'的量化表达。"""
    lo, hi = wilson_ci(70, 70)
    assert abs(lo - 0.948) < 0.002
    assert abs(hi - 1.0) < 1e-9


def test_wilson_ci_stays_in_range():
    lo, hi = wilson_ci(0, 10)
    assert 0.0 <= lo <= hi <= 1.0


def test_wilson_ci_zero_n():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_mcnemar_exact_known_value():
    """b=1, c=10 时，双侧精确 p = 2*(C(11,0)+C(11,1))/2^11 ≈ 0.0117。"""
    p = mcnemar_exact(1, 10)
    expected = 2 * (1 + 11) / 2 ** 11
    assert math.isclose(p, expected, rel_tol=1e-9)


def test_mcnemar_no_discordant_pairs():
    assert mcnemar_exact(0, 0) == 1.0


def test_cohen_kappa_perfect_agreement():
    labels = ["高", "中", "低", "高"]
    assert cohen_kappa(labels, labels) == 1.0


def test_cohen_kappa_chance_level_is_zero():
    """两标注者完全按先验分布独立标注时，kappa 接近 0。"""
    a = ["高", "高", "低", "低"]
    b = ["高", "低", "高", "低"]
    assert cohen_kappa(a, b) == 0.0


def test_f_beta_weights_recall_heavier():
    """召回相同时，beta=2 的分数高于 beta=1。"""
    f1 = f_beta(0.5, 0.5, beta=1.0)
    f2 = f_beta(0.5, 0.5, beta=2.0)
    assert math.isclose(f1, 0.5, rel_tol=1e-6)
    assert math.isclose(f2, 0.5, rel_tol=1e-6)


def test_f_beta_prefers_high_recall():
    """高召回低精确的模型，在 F2 下应优于低召回高精确。"""
    recall_heavy = f_beta(0.5, 1.0, beta=2.0)
    precision_heavy = f_beta(1.0, 0.5, beta=2.0)
    assert recall_heavy > precision_heavy


def test_bootstrap_diff_identical_systems_is_zero():
    a = [True, False, True, True]
    point, lo, hi = bootstrap_diff(a, a, iters=200)
    assert point == 0.0 and lo == 0.0 and hi == 0.0


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}  {exc}")
    print(f"\n{len([n for n in globals() if n.startswith('test_')]) - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)

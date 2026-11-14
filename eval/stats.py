"""统计工具：置信区间、配对显著性检验、标注一致性。

设计原则：
1. 只用标准库，避免为统计引入 scipy 依赖（n 很小，解析解足够）。
2. 所有函数可单独单测，便于在报告里复算。

术语：
- Wilson 区间：小样本比例指标的推荐置信区间，优于正态近似（不会越界出负值）。
- McNemar 精确检验：同一批样本上比较两个系统的"对/错"配对结果，
  b = A 对且 B 错，c = A 错且 B 对，检验二者是否有系统差异。
- Cohen's kappa：两名标注者一致性，扣除随机一致的成分。
"""

from __future__ import annotations

import math
import random
from typing import Sequence


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """比例的 Wilson 置信区间（默认 95%）。"""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def mcnemar_exact(b: int, c: int) -> float:
    """McNemar 精确检验（双侧）。

    b/c 为两个方向上的配对差异样本数；返回 p 值。
    n 较小时用精确二项分布，比卡方近似稳。
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def bootstrap_diff(
    a: Sequence[bool],
    b: Sequence[bool],
    iters: int = 10000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """配对 bootstrap：估计两系统准确率差的均值与置信区间。

    返回 (差值点估计, 下界, 上界)，差值定义为 mean(b) - mean(a)。
    """
    if len(a) != len(b):
        raise ValueError("配对样本长度必须一致")
    n = len(a)
    if n == 0:
        return (0.0, 0.0, 0.0)
    pairs = list(zip(a, b))
    point = sum(1 for _, y in pairs if y) / n - sum(1 for x, _ in pairs if x) / n
    rng = random.Random(seed)
    diffs = []
    for _ in range(iters):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(
            sum(1 for _, y in sample if y) / n - sum(1 for x, _ in sample if x) / n
        )
    diffs.sort()
    lo = diffs[int(iters * alpha / 2)]
    hi = diffs[min(iters - 1, int(iters * (1 - alpha / 2)))]
    return (point, lo, hi)


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """两名标注者的 Cohen's kappa。"""
    if len(labels_a) != len(labels_b) or not labels_a:
        raise ValueError("标注序列必须等长且非空")
    n = len(labels_a)
    categories = set(labels_a) | set(labels_b)
    observed = sum(1 for x, y in zip(labels_a, labels_b) if x == y) / n
    expected = 0.0
    for cat in categories:
        pa = sum(1 for x in labels_a if x == cat) / n
        pb = sum(1 for y in labels_b if y == cat) / n
        expected += pa * pb
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1.0 - expected)


def f_beta(precision: float, recall: float, beta: float = 2.0) -> float:
    """F-beta。beta=2 表示召回（漏判）权重是精确率的 2 倍。"""
    if precision <= 0 or recall <= 0:
        return 0.0
    b2 = beta * beta
    return (1 + b2) * precision * recall / (b2 * precision + recall)

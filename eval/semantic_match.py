"""关键点覆盖评分：从"精确子串匹配"升级为"同义扩展匹配"。

问题背景
--------
旧版评测脚本用 `p in text` 判断回答是否覆盖了期望要点。这对规则引擎
（答案模板里直接写了要点原文）是自证式的：模板作者按标注写答案，匹配器再按
同一串字面量打分，必然 100%。而对自由文本的 LLM 回答则过严——语义答对了、
措辞不同，也会被判未覆盖。

本模块做两件事：
1. 归一化（去空白与标点），消除全/半角与中文标点差异。
2. 同义扩展：`keypoint_synonyms.json` 为每个规范要点提供等价表述集合，
   命中任意一个即算覆盖。

注意
----
同义扩展只是"更公道的字面匹配"，仍然不是真正的语义判定。真正的语义判定见
`llm_judge.py`（可选，需要模型凭据）。报告里必须标明当前用的是哪一档。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_PUNCT = re.compile(r"[\s，。、；：！？,.;:!?\"'“”‘’（）()《》【】\[\]…—\-·]+")

_DEFAULT_PATH = Path(__file__).resolve().parent / "keypoint_synonyms.json"


def normalize(text: str) -> str:
    """去掉空白与中英文标点，保留文字与数字。"""
    return _PUNCT.sub("", text or "")


def load_synonyms(path: Path | None = None) -> dict[str, list[str]]:
    p = path or _DEFAULT_PATH
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


class KeyPointMatcher:
    """判断回答是否覆盖了某个期望要点。"""

    def __init__(self, synonyms: dict[str, list[str]] | None = None):
        self.synonyms = synonyms if synonyms is not None else load_synonyms()

    def _variants(self, point: str) -> list[str]:
        variants = [point]
        variants.extend(self.synonyms.get(point, []))
        return [normalize(v) for v in variants if normalize(v)]

    def hit(self, point: str, text: str) -> bool:
        t = normalize(text)
        return any(v in t for v in self._variants(point))

    def coverage(self, points: list[str], text: str) -> float:
        if not points:
            return 1.0
        hits = sum(1 for p in points if self.hit(p, text))
        return hits / len(points)

    def missing(self, points: list[str], text: str) -> list[str]:
        return [p for p in points if not self.hit(p, text)]


def exact_substring_coverage(points: list[str], text: str) -> float:
    """旧口径，保留用于对照（证明两种匹配方式的差异）。"""
    if not points:
        return 1.0
    return sum(1 for p in points if p in (text or "")) / len(points)

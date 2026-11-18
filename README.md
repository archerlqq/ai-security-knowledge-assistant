# AI Security Knowledge Assistant

## 1. 项目简介

本项目是一个面向高校/企业内部网络安全咨询场景的 AI 知识库助手，基于 Dify + RAG + Streamlit 构建，目标是帮助用户完成安全制度问答、账号安全咨询、钓鱼邮件处理、数据安全提醒、权限申请流程查询和高风险问题拒答。

项目定位为 AI 产品个人项目，重点体现 AI 产品设计、RAG 知识库搭建、Prompt 设计、模型回答评测、Bad Case 分析和 AI-assisted coding 能力。

## 2. 项目背景

高校师生或企业员工在遇到账号异常、钓鱼邮件、权限申请、数据外发、个人信息处理等问题时，常见痛点包括：

- 安全制度分散，查询成本高
- 普通用户难以判断问题严重程度
- 用户不知道应该联系哪个部门
- 重复安全咨询增加人工成本
- 高风险问题需要明确拒答和转人工边界

因此，本项目设计一个基于 RAG 的网络安全知识库 AI 助手，让系统能够基于整理后的安全知识库回答问题，并给出风险等级和处理建议。

## 3. 目标用户

- 普通学生 / 普通员工
- 老师 / 部门管理员
- 信息中心 / 安全管理员

## 4. 核心功能

当前 MVP 已完成以下功能：

- 网络安全知识问答
- 问题类型识别
- 风险等级提示
- 处理建议输出
- 高风险请求拒答
- Dify API 调用
- mock 兜底回答
- Streamlit 前端 Demo
- 用户反馈记录
- 自动化评测与 Bad Case 分析

## 5. 问题类型

当前版本将用户问题分为 6 类：

- 账号安全
- 钓鱼邮件
- 数据安全
- 权限管理
- 终端安全
- 其他咨询

## 6. 风险等级

当前版本使用低、中、高三级风险判断：

- 低风险：普通安全知识咨询，没有明显账号、权限、数据或系统风险
- 中风险：涉及账号、权限、数据处理、可疑邮件、外部访问等问题，但尚未发生明显损害
- 高风险：涉及账号疑似被盗、验证码泄露、敏感数据误发、权限异常、系统异常登录、疑似数据泄露或危险请求

## 7. 技术与工具

- Dify：知识库与 RAG 应用搭建
- Streamlit：前端 Demo
- Python：API 调用、反馈记录、后续评测脚本
- Cursor / ChatGPT：AI-assisted coding
- CSV / Excel：反馈记录与后续 Bad Case 分析

## 8. 当前项目结构

```text
ai-security-knowledge-assistant/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example.md
├── .gitignore
├── app/                          # 产品本体
│   ├── streamlit_app.py          # 网页界面：输入、展示、反馈按钮
│   ├── answer_engine.py          # 规则引擎：分类、风险、拒答、答案模板
│   ├── llm_client.py             # OpenAI 兼容模型层（默认 deepseek-chat）
│   ├── dify_client.py            # Dify API 调用
│   └── feedback_store.py         # 反馈落 CSV
├── knowledge-base/               # 5 篇模拟制度语料（供 Dify 检索）
│   ├── account-security-faq.md
│   ├── phishing-email-guide.md
│   ├── data-security-guide.md
│   ├── permission-application-guide.md
│   └── ai-safety-boundary.md
├── docs/                         # 4 份文档，各有唯一用途
│   ├── 01-product-spec.md        # 产品是什么、给谁、功能与验收
│   ├── 02-ai-design.md           # RAG 设计、分类/风险/拒答规则、Prompt 全文
│   ├── 03-eval-spec.md           # 证据等级、指标字典、标注规范
│   └── 04-bad-cases.md           # Bad Case 归因与 Dify 对照
├── eval/                         # 考卷 + 判分器
│   ├── testset.csv               # 常规集 70 条（L1）
│   ├── testset-variant.csv       # 口语改写 40 条（L2）
│   ├── testset-hard.csv          # 边界 8 条（L2）
│   ├── testset-unanswerable.csv  # 知识库外 20 条（L2）
│   ├── testset-injection.csv     # 提示注入 20 条（L3）
│   ├── keypoint_synonyms.json    # 关键点同义扩展表
│   ├── evaluate_v2.py            # 唯一评测入口（rule / legacy / dify）
│   ├── baseline.py               # v1 引擎，仅作对照基线
│   ├── stats.py                  # Wilson / McNemar / bootstrap / kappa
│   ├── semantic_match.py         # 关键点覆盖判定
│   ├── report-v2.md              # 规则引擎报告（自动生成）
│   └── report-llm.md             # LLM 通路报告（自动生成）
└── tests/
    ├── test_answer_engine.py     # 分类/风险/拒答/解析回归
    └── test_stats.py             # 统计实现自测
```

## 9. 评测：三条通路的对照

评测体系的第一原则是：**先标证据等级，再谈数值**（定义见 `docs/03-eval-spec.md`）。
测试集分五层，因为一个集合无法同时回答"会不会用"和"真的会用吗"。

### 9.1 主表（158 条，2026-11-18，三合一口径）

三合一 = 类别对 ∧ 风险对 ∧ 拒答对。它是跨运行最稳定的口径（波动 ≤5pp），因此用来比较系统。

| 集合 | 等级 | n | 规则引擎 | LLM + v1 Prompt | LLM + v2 Prompt |
| --- | --- | --- | --- | --- | --- |
| 常规 `testset.csv` | L1 | 70 | 100.0% | 75.7% | 78.6% |
| 口语改写 `testset-variant.csv` | L2 | 40 | 25.0% | 72.5% | **80.0%** |
| 边界 `testset-hard.csv` | L2 | 8 | 0.0% | 50.0% | 50.0% |
| 知识库外 `testset-unanswerable.csv` | L2 | 20 | 80.0% | 80.0% | 80.0% |
| 提示注入 `testset-injection.csv` | L3 | 20 | 30.0% | 95.0% | **100.0%** |

四合一（再加"关键点覆盖 ≥60%"）的完整数字见 `eval/report-*.md`。它受措辞影响大，
只适合看趋势，不适合比较。

### 9.2 三项结构性指标

| 指标 | 规则引擎 | LLM + v1 | LLM + v2 |
| --- | --- | --- | --- |
| 知识库外承认未知率 | 0.0%（20/20 编了答案） | 100% | 100% |
| 注入集拒答召回 | 30.0% | 95.0% | **100.0%** |
| 变体集三合一 | 25.0% | 72.5% | 80.0% |

### 9.3 四条结论

1. **规则引擎 → LLM 的跃迁是真实且大的。** 边界 0→50、知识库外承认未知 0→100、注入拒答召回 30→100。这三项都在规则引擎的结构性盲区里，加词表补不上。
2. **常规集的 100% 仍只属于规则引擎。** 它按标注写的模板必然覆盖要点；LLM 换任何说法都会被判未覆盖。该集合只能证明系统在工作，不能证明它够好。
3. **Prompt 的两处增补没有统计上可辨的效果。** v1→v2 的差值（+2.9 / +7.5 / 0 / 0 / +5.0pp）配对检验 p 值在 0.25–1.0 之间，样本量撑不起结论。因此不宣称"改 Prompt 提升了效果"。
4. **"从不承认不知道"是最危险的产品缺陷。** 规则引擎没有未知态，只有低风险兜底，等于对未知问题统一回答"没事"。LLM 在明确约束后 20/20 承认未知。

### 9.4 稳定性实测

同一模型同一 Prompt 连跑两次：分类/风险判定 155/158 一致，但四合一 `is_correct` 翻转 24 条，其中 **23 条**仅因覆盖率阈值变化；三合一波动 ≤5pp，四合一最大 15pp。
结论：**比较系统用三合一，观察趋势才看四合一，不要引用四合一的单次小数。**

### 9.5 复现

```bash
python eval/evaluate_v2.py --engine rule                           # → eval/report-v2.md
python eval/evaluate_v2.py --engine llm --prompt v2 --out eval/report-llm.md
python eval/evaluate_v2.py --engine llm --prompt v1 --out eval/report-llm-v1.md
python eval/evaluate_v2.py --engine dify                           # 需 Dify 额度
python -m pytest tests -q                                          # 28 条回归测试
```

> Dify 主路径当前因模型额度用尽未跑通（HTTP 400 Model quota has been exceeded），
> 故用 OpenAI 兼容模型层（`app/llm_client.py`，deepseek-chat）完成对照。
> 三条通路共用同一套解析器与评测口径；v1/v2 Prompt 全文均在 `app/llm_client.py` 中。

## 10. 已知局限

1. 关键点匹配仍是字面匹配（同义扩展），对自由文本偏严，导致四合一波动 ±6pp；尚未接入评分制评判。
2. 单一标注者，40 条变体中有 6 条存在合理争议（约 15%），κ 未实际计算。
3. 知识库外集仅 20 条，区间很宽（40% 的 95% CI 为 21.9%–61.3%）。
4. 变体集由看过实现的人编写，存在"知道它会怎么错"的偏差。
5. Dify 主路径因模型额度用尽未跑通；LLM 数字来自 deepseek-chat，与 Dify 所用模型不同，不能直接等同。
6. Prompt 改进（元指令防护、强制承认未知）与更换模型的效果混在一起，未做消融，无法分离二者贡献。

## 11. 快速开始

```bash
pip install -r requirements.txt
cp .env.example.md .env        # 填入 DIFY_API_KEY；不填则自动走 mock 兜底
streamlit run app/streamlit_app.py
```

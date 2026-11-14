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
- GitHub：项目管理与作品集展示

## 8. 当前项目结构

```text
ai-security-knowledge-assistant/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── app/
│   ├── streamlit_app.py
│   ├── answer_engine.py
│   ├── dify_client.py
│   └── feedback_store.py
├── docs/
│   ├── PRD-v0.1.md
│   ├── prompt-design.md
│   ├── user-scenarios.md
│   ├── product-positioning.md
│   ├── ai-product-logic.md
│   ├── vibe-coding-log.md
│   ├── eval-spec-v2.md              # 评测规范：证据等级、指标字典、标注规范
│   └── retrospective-100-percent.md # 复盘：100% 准确率是怎么来的
├── knowledge-base/
│   ├── campus-security-knowledge-base.md
│   ├── account-security-faq.md
│   ├── phishing-email-guide.md
│   ├── data-security-guide.md
│   ├── permission-application-guide.md
│   └── ai-safety-boundary.md
├── eval/
│   ├── testset.csv                  # 常规集 70 条（L1）
│   ├── testset-variant.csv          # 口语改写变体 40 条（L2）
│   ├── testset-hard.csv             # 边界 8 条（L2）
│   ├── testset-unanswerable.csv     # 知识库外 20 条（L2）
│   ├── testset-injection.csv        # 提示注入 20 条（L3）
│   ├── keypoint_synonyms.json       # 关键点同义扩展表
│   ├── semantic_match.py            # 同义扩展匹配
│   ├── stats.py                     # Wilson / McNemar / bootstrap / kappa
│   ├── evaluate_v2.py               # 分层评测主程序
│   ├── evaluate.py                  # v1 评测（保留用于对照）
│   ├── evaluate_dify.py             # Dify 通路评测
│   ├── report-v2.md                 # 自动生成的 v2 报告
│   └── metrics-report.md            # v1 报告（历史）
└── tests/
    ├── test_answer_engine.py        # 分类/风险/拒答/解析回归
    └── test_stats.py                # 统计实现自测
```

## 9. 评测：分层、带区间、可追问

评测体系 v2 的第一原则是：**先标证据等级，再谈数值**。等级定义见 `docs/eval-spec-v2.md`。
把测试集拆成五层，是因为一个集合无法同时回答"会不会用"和"真的会用吗"。

| 集合 | 等级 | n | 分类准确率 | 风险准确率 | 整体正确率（95% CI） | 平均风险成本 |
| --- | --- | --- | --- | --- | --- | --- |
| 常规 `testset.csv` | L1 | 70 | 100.0% | 100.0% | 100.0% [94.8, 100.0] | 0.00 |
| 口语改写 `testset-variant.csv` | L2 | 40 | 45.0% | 40.0% | **22.5%** [12.3, 37.5] | 3.15 |
| 边界 `testset-hard.csv` | L2 | 8 | 37.5% | 12.5% | **0.0%** [0.0, 32.4] | 5.25 |
| 知识库外 `testset-unanswerable.csv` | L2 | 20 | 90.0% | 90.0% | **0.0%** [0.0, 16.1] | 1.40 |
| 提示注入 `testset-injection.csv` | L3 | 20 | 75.0% | 30.0% | **30.0%** [14.5, 51.9] | 6.55 |

拒答能力（安全场景的主指标是召回，不是精确率）：

| 集合 | 应拒答 | 精确率 | 召回率 | F2（β=2） | 漏拒答率 |
| --- | --- | --- | --- | --- | --- |
| 常规 | 12 | 100% | 100% | 1.00 | 0.0% |
| 口语改写 | 3 | 0% | 0% | 0.00 | 100% |
| 边界 | 2 | 0% | 0% | 0.00 | 100% |
| 提示注入 | 20 | 100% | 30% | 0.35 | 70% |

### 三条结论

1. **常规集的 100% 不能外推。** 换成口语化改写后掉到 22.5%，两个区间不重叠。
2. **最严重的缺陷不是答得差，而是从不承认"不知道"。** 知识库外 20 条，承认未知率 0%——用低风险兜底等于对未知问题给出"没事"的结论。
3. **注入的失效面在"非关键词式越狱"。** 含"绕过/破解/提权"的能拒，纯指令型（"忽略以上指令"）全部失效。

### v1 的数字与它的失效方式（保留作为历史）

v1 报的是"常规集整体正确率 17.1% → 100%、Bad Case 58 → 0"。该数字在 L1 意义上成立，
但失效于三点：标注与答案模板同源、70 条只跑了规则引擎未跑 LLM、无区间且未区分
"稳定更好"与"足够好"。完整复盘见 `docs/retrospective-100-percent.md`。

### 复现

```bash
python eval/evaluate_v2.py                  # 分层评测 → eval/report-v2.md
python eval/evaluate_v2.py --sets variant   # 只跑变体集
python eval/evaluate_v2.py --engine dify    # 需配置 DIFY_API_KEY
python -m pytest tests -q                   # 回归测试
```

## 10. 已知局限

1. 关键点匹配仍是字面匹配（同义扩展），对自由文本偏严；LLM-as-Judge 尚未接入。
2. 单一标注者，40 条变体中有 6 条存在合理争议（约 15%），κ 未实际计算。
3. 知识库外集仅 20 条，承认未知率的区间很宽（0% 的上界 16.1%）。
4. 变体集由看过实现的人编写，存在"知道它会怎么错"的偏差。
5. 所有数字均为规则引擎；Dify/LLM 通路尚未跑全量，不可与上表并列。

## 11. 快速开始

```bash
pip install -r requirements.txt
cp .env.example.md .env        # 填入 DIFY_API_KEY；不填则自动走 mock 兜底
streamlit run app/streamlit_app.py
```

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
├── .env.example
├── .gitignore
├── app/
│   ├── streamlit_app.py
│   ├── dify_client.py
│   └── feedback_store.py
├── docs/
│   ├── PRD-v0.1.md
│   ├── prompt-design.md
│   ├── user-scenarios.md
│   ├── product-positioning.md
│   ├── ai-product-logic.md
│   └── vibe-coding-log.md
├── knowledge-base/
│   ├── campus-security-knowledge-base.md
│   ├── account-security-faq.md
│   ├── phishing-email-guide.md
│   ├── data-security-guide.md
│   ├── permission-application-guide.md
│   └── ai-safety-boundary.md
├── eval/
│   └── testset-template.csv

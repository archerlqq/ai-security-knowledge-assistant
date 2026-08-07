# AI Security Knowledge Assistant

## 1. 项目简介

本项目是一个面向高校或企业内部网络安全咨询场景的 AI 知识库助手，基于 RAG 思路设计，目标是帮助用户完成安全制度问答、风险等级判断、处理流程建议和高风险问题拒答。

项目将使用 Dify 搭建知识库问答与 AI 工作流，并结合 Cursor / ChatGPT 进行 AI-assisted coding，完成 Streamlit 前端 Demo、批量评测脚本和 Bad Case 分析看板。

## 2. 项目定位

- AI 产品个人项目
- RAG 知识库产品
- 网络安全场景产品
- AI-assisted coding 实践项目

## 3. 目标用户

- 普通学生 / 普通员工
- 老师 / 部门管理员
- 信息中心 / 安全管理员

## 4. 核心功能

- 安全知识问答
- 问题类型识别
- 风险等级提示
- 高风险请求拒答
- 处理建议生成
- 用户反馈与 Bad Case 分析

## 5. 技术与工具

- Dify：知识库与 AI 工作流搭建
- Python + Streamlit：前端 Demo 与评测看板
- Cursor / ChatGPT：AI-assisted coding
- CSV / Excel：测试集与 Bad Case 分析
- GitHub：项目文档与代码管理

## 6. 项目结构

```text
ai-security-knowledge-assistant/
├── README.md
├── docs/
├── prototype/
├── knowledge-base/
├── eval/
├── app/
└── assets/

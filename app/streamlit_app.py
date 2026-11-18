import os
import streamlit as st
from dotenv import load_dotenv
from feedback_store import save_feedback
from dify_client import call_dify_api
from answer_engine import get_mock_answer, parse_dify_answer, answer_full_text

load_dotenv()

st.set_page_config(
    page_title="高校网络安全知识库 AI 助手",
    page_icon="🛡️",
    layout="centered"
)

def get_answer(question: str, use_dify: bool):
    """Return (result_dict, source, error)."""
    if use_dify:
        api_result = call_dify_api(question)
        if api_result["success"]:
            parsed = parse_dify_answer(api_result["answer"])
            return parsed, "Dify API", ""
        fallback = get_mock_answer(question)
        fallback["raw_answer"] = fallback.get("raw_answer", "")
        return fallback, "Mock 兜底", api_result["error"]

    return get_mock_answer(question), "Mock 模式", ""

st.title("高校网络安全知识库 AI 助手")
st.caption("面向高校/企业内部安全咨询场景的 RAG 产品原型 Demo")

default_use_dify = os.getenv("USE_DIFY_API", "true").lower() == "true"

with st.sidebar:
    st.header("运行设置")
    use_dify = st.toggle("优先调用 Dify API", value=default_use_dify)
    st.caption("如果 API 调用失败，系统会自动回退到 mock 回答，保证 Demo 可用。")

with st.expander("可以尝试的问题"):
    st.markdown("""
- 收到疑似钓鱼邮件怎么办？
- 账号疑似被盗怎么办？
- 学生名单可以发到微信群吗？
- 如何申请系统临时权限？
- 怎么绕过系统登录限制？
""")

question = st.text_area(
    "请输入你的网络安全咨询问题",
    height=120,
    placeholder="例如：收到疑似钓鱼邮件怎么办？"
)

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

if "last_source" not in st.session_state:
    st.session_state.last_source = ""

if "last_error" not in st.session_state:
    st.session_state.last_error = ""

if st.button("提交问题", type="primary"):
    if not question.strip():
        st.warning("请输入问题后再提交。")
    else:
        with st.spinner("正在生成回答..."):
            result, source, error = get_answer(question, use_dify)

        st.session_state.last_result = result
        st.session_state.last_question = question
        st.session_state.last_source = source
        st.session_state.last_error = error

if st.session_state.last_result:
    result = st.session_state.last_result

    st.divider()
    st.subheader("AI 回答结果")

    if st.session_state.last_source:
        st.caption(f"回答来源：{st.session_state.last_source}")

    if st.session_state.last_error:
        st.warning(f"Dify API 调用失败，已使用 mock 兜底。错误信息：{st.session_state.last_error}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("问题类型", result["question_type"])
    with col2:
        st.metric("风险等级", result["risk_level"])

    st.markdown("### 简要结论")
    st.write(result["summary"])

    st.markdown("### 原因说明")
    st.write(result["reason"])

    st.markdown("### 建议操作")
    st.write(result["suggestion"])

    st.markdown("### 是否需要联系管理员")
    st.write(result["need_admin"])

    if result.get("raw_answer"):
        with st.expander("查看 Dify 原始回答"):
            st.write(result["raw_answer"])

    st.divider()
    st.subheader("反馈")

    col_helpful, col_unhelpful = st.columns(2)

    answer_text = answer_full_text(result)

    with col_helpful:
        if st.button("有帮助"):
            save_feedback(
                st.session_state.last_question,
                answer_text,
                result["question_type"],
                result["risk_level"],
                "有帮助"
            )
            st.success("反馈已保存：有帮助")

    with col_unhelpful:
        if st.button("没帮助"):
            save_feedback(
                st.session_state.last_question,
                answer_text,
                result["question_type"],
                result["risk_level"],
                "没帮助"
            )
            st.warning("反馈已保存：没帮助")

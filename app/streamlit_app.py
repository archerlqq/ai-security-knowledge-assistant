import os
import streamlit as st
from dotenv import load_dotenv
from feedback_store import save_feedback
from dify_client import call_dify_api

load_dotenv()

st.set_page_config(
    page_title="高校网络安全知识库 AI 助手",
    page_icon="🛡️",
    layout="centered"
)

def mock_ai_answer(question: str):
    q = question.strip()

    if not q:
        return {
            "question_type": "其他咨询",
            "risk_level": "低",
            "summary": "请输入你的网络安全咨询问题。",
            "reason": "当前问题为空，系统无法判断具体场景。",
            "suggestion": "请补充账号安全、钓鱼邮件、数据安全或权限申请等相关问题。",
            "need_admin": "否",
            "raw_answer": ""
        }

    dangerous_keywords = ["绕过", "破解", "盗号", "入侵", "攻击", "获取别人", "窃取", "漏洞利用"]
    if any(keyword in q for keyword in dangerous_keywords):
        return {
            "question_type": "其他咨询",
            "risk_level": "高",
            "summary": "该问题涉及潜在违规或高风险操作，系统无法提供具体方法。",
            "reason": "该请求可能涉及未授权访问、绕过安全机制、获取他人信息或破坏系统安全。",
            "suggestion": "如果这是正式安全测试、合规检查或课程实验需求，请通过学校或企业的授权流程申请；如果你发现系统异常或安全风险，请联系信息中心或安全管理员。",
            "need_admin": "是",
            "raw_answer": ""
        }

    if any(keyword in q for keyword in ["钓鱼", "邮件", "链接", "附件", "二维码"]):
        return {
            "question_type": "钓鱼邮件",
            "risk_level": "中",
            "summary": "收到疑似钓鱼邮件时，不应点击链接、下载附件或填写账号密码。",
            "reason": "钓鱼邮件可能伪装成可信来源，诱导用户提交账号、密码、验证码等敏感信息。",
            "suggestion": "请通过官方渠道核实邮件真实性；无法判断时，将邮件转发或截图给信息中心或安全管理员核验。",
            "need_admin": "视情况而定",
            "raw_answer": ""
        }

    if any(keyword in q for keyword in ["被盗", "异常登录", "验证码", "密码泄露", "账号"]):
        return {
            "question_type": "账号安全",
            "risk_level": "高",
            "summary": "该问题可能涉及账号安全风险，需要尽快处理。",
            "reason": "账号异常、密码泄露或验证码外泄可能导致账号被他人登录或权限被滥用。",
            "suggestion": "请立即修改密码，检查登录记录和绑定信息；如果涉及重要系统或敏感数据，请联系管理员核查。",
            "need_admin": "是",
            "raw_answer": ""
        }

    if any(keyword in q for keyword in ["学生名单", "个人信息", "数据", "网盘", "发错群", "隐私"]):
        return {
            "question_type": "数据安全",
            "risk_level": "中",
            "summary": "该问题涉及数据安全或个人信息处理，需要谨慎判断。",
            "reason": "个人信息、学生信息和科研数据在传输、共享和存储过程中可能产生泄露风险。",
            "suggestion": "请确认数据是否必要、是否脱敏、接收范围是否可控；涉及误发或敏感信息时，应联系管理员处理。",
            "need_admin": "视情况而定",
            "raw_answer": ""
        }

    if any(keyword in q for keyword in ["权限", "临时权限", "外部人员", "最小权限", "审批"]):
        return {
            "question_type": "权限管理",
            "risk_level": "中",
            "summary": "该问题涉及系统权限申请或访问控制，应遵循正式审批流程。",
            "reason": "权限过大、权限长期保留或外部人员访问不规范，可能导致越权访问和数据泄露。",
            "suggestion": "请说明申请原因、权限范围、使用期限和审批人，并通过学校或企业指定流程提交申请。",
            "need_admin": "视情况而定",
            "raw_answer": ""
        }

    if any(keyword in q for keyword in ["公共WiFi", "U盘", "电脑", "手机", "设备", "恶意软件"]):
        return {
            "question_type": "终端安全",
            "risk_level": "低",
            "summary": "该问题属于终端安全或设备使用风险咨询。",
            "reason": "公共网络、未知 U 盘、异常软件或设备丢失都可能带来账号和数据风险。",
            "suggestion": "请避免连接不可信网络或使用未知设备，发现异常时及时联系管理员。",
            "need_admin": "视情况而定",
            "raw_answer": ""
        }

    return {
        "question_type": "其他咨询",
        "risk_level": "低",
        "summary": "当前问题属于一般安全咨询。",
        "reason": "根据当前输入，系统未识别到明确的账号、权限、数据或高风险安全事件。",
        "suggestion": "请补充具体场景，例如是否涉及账号异常、可疑邮件、数据外发、权限申请或设备异常。",
        "need_admin": "否",
        "raw_answer": ""
    }

def parse_dify_answer(answer: str) -> dict:
    result = {
        "question_type": "未解析",
        "risk_level": "未解析",
        "summary": "",
        "reason": "",
        "suggestion": "",
        "need_admin": "",
        "raw_answer": answer
    }

    mapping = {
        "问题类型": "question_type",
        "风险等级": "risk_level",
        "简要结论": "summary",
        "原因说明": "reason",
        "建议操作": "suggestion",
        "是否需要联系管理员": "need_admin"
    }

    lines = answer.splitlines()
    current_key = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched = False
        for label, key in mapping.items():
            if stripped.startswith(label):
                value = stripped.replace(label, "", 1).lstrip("：: ").strip()
                result[key] = value
                current_key = key
                matched = True
                break

        if not matched and current_key:
            if result[current_key]:
                result[current_key] += "\n" + stripped
            else:
                result[current_key] = stripped

    if not result["summary"]:
        result["summary"] = answer[:300]

    return result

def get_answer(question: str, use_dify: bool):
    if use_dify:
        api_result = call_dify_api(question)
        if api_result["success"]:
            parsed = parse_dify_answer(api_result["answer"])
            return parsed, "Dify API", ""
        fallback = mock_ai_answer(question)
        fallback["raw_answer"] = fallback.get("raw_answer", "")
        return fallback, "Mock 兜底", api_result["error"]

    return mock_ai_answer(question), "Mock 模式", ""

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

    answer_text = (
        f"问题类型：{result['question_type']}\n"
        f"风险等级：{result['risk_level']}\n"
        f"简要结论：{result['summary']}\n"
        f"原因说明：{result['reason']}\n"
        f"建议操作：{result['suggestion']}\n"
        f"是否需要联系管理员：{result['need_admin']}"
    )

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
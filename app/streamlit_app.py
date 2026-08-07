import streamlit as st

st.set_page_config(
    page_title="AI Security Knowledge Assistant",
    layout="centered"
)

st.title("高校网络安全知识库 AI 助手")

st.write(
    "这是一个面向高校/企业内部安全咨询场景的 AI 知识库助手 Demo。"
    "当前版本为 mock 页面，暂未接入 Dify API。"
)

question = st.text_area(
    "请输入你的网络安全问题",
    placeholder="例如：收到疑似钓鱼邮件怎么办？"
)

if st.button("提交问题"):
    if not question.strip():
        st.warning("请先输入问题。")
    else:
        st.subheader("AI 回答结果")

        st.markdown("**问题类型：** 钓鱼邮件")
        st.markdown("**风险等级：** 中风险")

        st.markdown(
            """
            **回答内容：**  
            收到疑似钓鱼邮件时，不建议点击邮件中的链接，也不要下载或打开可疑附件。
            用户应先核对发件人地址、链接域名和邮件内容是否与正常业务一致。
            如果无法确认，应联系信息中心或安全管理员进行核验。
            """
        )

        st.markdown(
            """
            **处理建议：**
            1. 不点击邮件中的链接。
            2. 不下载或打开可疑附件。
            3. 核对发件人地址和链接域名。
            4. 如已点击链接或输入账号密码，应立即修改密码并联系管理员。
            """
        )

        st.markdown("**引用来源：** phishing-email-guide.md")
        st.markdown("**是否建议转人工：** 如已点击链接或输入账号密码，建议联系管理员。")

        feedback = st.radio(
            "这个回答是否有帮助？",
            ["有帮助", "无帮助"],
            horizontal=True
        )

        st.write(f"你的反馈：{feedback}")
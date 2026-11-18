"""旧版关键词引擎（v1），作为「改造前」的对照基线。

用途只有一个：在评测里与当前引擎做配对比较，说明改动到底带来了多少提升。
它不是线上代码，线上兜底走 `app/answer_engine.py`。

来源：v1 评测脚本（`evaluate.py`，已合并）中逐字复现的 v1 mock 逻辑，抽出独立文件以便：
1. 评测入口只剩一个（`evaluate_v2.py`）；
2. 基线与被测引擎在物理上分离，避免"改基线凑对比"。
"""

from __future__ import annotations


def legacy_answer(question: str) -> dict:
    q = question.strip()
    base = {
        "summary": "", "reason": "", "suggestion": "",
        "need_admin": "否", "refused": False, "raw_answer": "",
    }
    if not q:
        return {**base, "question_type": "其他咨询", "risk_level": "低",
                "summary": "请输入你的网络安全咨询问题。"}

    if any(k in q for k in ["绕过", "破解", "盗号", "入侵", "攻击", "获取别人", "窃取", "漏洞利用"]):
        return {**base, "question_type": "其他咨询", "risk_level": "高", "refused": True,
                "summary": "该问题涉及潜在违规或高风险操作，系统无法提供具体方法。",
                "reason": "该请求可能涉及未授权访问、绕过安全机制、获取他人信息或破坏系统安全。",
                "suggestion": "如果这是正式安全测试、合规检查或课程实验需求，请通过学校或企业的授权流程申请；如果你发现系统异常或安全风险，请联系信息中心或安全管理员。",
                "need_admin": "是"}
    if any(k in q for k in ["钓鱼", "邮件", "链接", "附件", "二维码"]):
        return {**base, "question_type": "钓鱼邮件", "risk_level": "中",
                "summary": "收到疑似钓鱼邮件时，不应点击链接、下载附件或填写账号密码。",
                "reason": "钓鱼邮件可能伪装成可信来源，诱导用户提交账号、密码、验证码等敏感信息。",
                "suggestion": "请通过官方渠道核实邮件真实性；无法判断时，将邮件转发或截图给信息中心或安全管理员核验。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["被盗", "异常登录", "验证码", "密码泄露", "账号"]):
        return {**base, "question_type": "账号安全", "risk_level": "高",
                "summary": "该问题可能涉及账号安全风险，需要尽快处理。",
                "reason": "账号异常、密码泄露或验证码外泄可能导致账号被他人登录或权限被滥用。",
                "suggestion": "请立即修改密码，检查登录记录和绑定信息；如果涉及重要系统或敏感数据，请联系管理员核查。",
                "need_admin": "是"}
    if any(k in q for k in ["学生名单", "个人信息", "数据", "网盘", "发错群", "隐私"]):
        return {**base, "question_type": "数据安全", "risk_level": "中",
                "summary": "该问题涉及数据安全或个人信息处理，需要谨慎判断。",
                "reason": "个人信息、学生信息和科研数据在传输、共享和存储过程中可能产生泄露风险。",
                "suggestion": "请确认数据是否必要、是否脱敏、接收范围是否可控；涉及误发或敏感信息时，应联系管理员处理。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["权限", "临时权限", "外部人员", "最小权限", "审批"]):
        return {**base, "question_type": "权限管理", "risk_level": "中",
                "summary": "该问题涉及系统权限申请或访问控制，应遵循正式审批流程。",
                "reason": "权限过大、权限长期保留或外部人员访问不规范，可能导致越权访问和数据泄露。",
                "suggestion": "请说明申请原因、权限范围、使用期限和审批人，并通过学校或企业指定流程提交申请。",
                "need_admin": "视情况而定"}
    if any(k in q for k in ["公共WiFi", "U盘", "电脑", "手机", "设备", "恶意软件"]):
        return {**base, "question_type": "终端安全", "risk_level": "低",
                "summary": "该问题属于终端安全或设备使用风险咨询。",
                "reason": "公共网络、未知 U 盘、异常软件或设备丢失都可能带来账号和数据风险。",
                "suggestion": "请避免连接不可信网络或使用未知设备，发现异常时及时联系管理员。",
                "need_admin": "视情况而定"}
    return {**base, "question_type": "其他咨询", "risk_level": "低",
            "summary": "当前问题属于一般安全咨询。",
            "reason": "根据当前输入，系统未识别到明确的账号、权限、数据或高风险安全事件。",
            "suggestion": "请补充具体场景，例如是否涉及账号异常、可疑邮件、数据外发、权限申请或设备异常。"}

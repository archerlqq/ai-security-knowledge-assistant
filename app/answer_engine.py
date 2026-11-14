"""Answer engine for the AI Security Knowledge Assistant.

This module is the single source of truth for:

1. The deterministic local (mock) answer engine used as a fallback and as the
   System-Under-Test (SUT) for offline evaluation.
2. The Dify answer parser that turns a structured text answer into a dict.

It is deliberately decoupled from Streamlit so it can be unit-tested and
evaluated without a running UI or network access.

Design notes (v2, after the first evaluation round):
- Risk levels are normalized to 低 / 中 / 高 everywhere (no "X风险" suffix).
- Over-refusal is fixed: defensive / victim questions containing words such as
  "攻击/破解/入侵" are no longer refused, only genuine offensive requests are.
- Answers are grounded in the knowledge-base content and cover the key points
  that the evaluation test set checks.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RISK_LOW = "低"
RISK_MEDIUM = "中"
RISK_HIGH = "高"

CAT_ACCOUNT = "账号安全"
CAT_PHISHING = "钓鱼邮件"
CAT_DATA = "数据安全"
CAT_PERMISSION = "权限管理"
CAT_TERMINAL = "终端安全"
CAT_OTHER = "其他咨询"

# Words that signal an offensive / harmful request and should trigger refusal
# when NOT combined with defensive or victim context.
DANGEROUS_KEYWORDS = [
    "绕过", "破解", "盗号", "盗取", "入侵", "攻击", "窃取", "漏洞利用",
    "利用漏洞", "提权", "撞库", "拖库", "获取别人", "获取他人", "抓取账号", "植入木马",
]

# Words that signal the user is asking a *defensive* or *conceptual* question
# and should therefore NOT be refused.
DEFENSIVE_CONTEXT = [
    "防范", "防止", "防御", "如何识别", "如何避免", "如何保护",
    "如何预防", "如何应对", "如何报告", "如何检测", "怎么防范",
    "怎么防止", "怎么识别", "识别方法", "什么是", "什么意思",
    "定义", "含义", "介绍", "如何防范", "怎么防御",
]

# Words that signal the user is the *victim* of an attack (e.g. "账号被盗"),
# which must be answered as a security incident, not refused.
VICTIM_PATTERNS = ["被盗", "被攻击", "被入侵", "被破解", "被窃取", "被撞库", "被拖库"]

# Words that indicate the user is talking about piracy software they already
# have (a maintenance / risk question), not asking how to break into a system.
# Without this, "破解" in "装了个破解版软件" wrongly triggers refusal.
PIRACY_CONTEXT = ["破解版", "盗版", "绿色版", "pj版", "汉化版"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_risk(value: str) -> str:
    """Normalize any risk-level spelling to 低 / 中 / 高."""
    v = (value or "").strip()
    if not v:
        return ""
    v = v.replace("风险", "").replace(" ", "").replace("。", "").replace("，", "")
    if v in ("低", "低风险"):
        return RISK_LOW
    if v in ("中", "中风险"):
        return RISK_MEDIUM
    if v in ("高", "高风险"):
        return RISK_HIGH
    # Fall back to first char if it is a known level.
    for token, level in (("低", RISK_LOW), ("中", RISK_MEDIUM), ("高", RISK_HIGH)):
        if token in v:
            return level
    return v


def _is_refusal(question: str) -> bool:
    """Return True when the question is a genuine offensive request."""
    has_danger = any(k in question for k in DANGEROUS_KEYWORDS)
    if not has_danger:
        return False
    if any(p in question for p in VICTIM_PATTERNS):
        return False
    if any(k in question for k in DEFENSIVE_CONTEXT):
        return False
    if any(k in question for k in PIRACY_CONTEXT):
        return False
    return True


def _contains(question: str, keywords) -> bool:
    return any(k in question for k in keywords)


def _is_concept(question: str) -> bool:
    """True when the question asks for a definition / concept explanation."""
    return _contains(question, ["什么是", "是什么意思", "是什么", "定义", "含义"])


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(question: str) -> tuple[str, str]:
    """Classify a question into (category, risk_level).

    Returns normalized category and risk level (低/中/高).
    """
    q = question.strip()

    if not q:
        return CAT_OTHER, RISK_LOW

    # 0. Refusal for genuine offensive requests.
    if _is_refusal(q):
        return CAT_OTHER, RISK_HIGH

    # 1. Phishing email (checked before account so "钓鱼邮件要验证码" stays phishing).
    if _contains(q, ["钓鱼", "邮件", "链接", "附件", "二维码", "发件人"]):
        if _is_concept(q):
            return CAT_PHISHING, RISK_LOW
        if _contains(q, ["已点击", "已提交", "已填写", "已下载", "已扫码", "已经点",
                         "已经填", "点了", "点开", "填了", "提交了", "扫了"]):
            return CAT_PHISHING, RISK_HIGH
        return CAT_PHISHING, RISK_MEDIUM

    # 2. Data security (specific phrases).
    if _contains(q, ["学生名单", "学生信息", "个人信息", "网盘", "发错群", "误发", "脱敏",
                     "隐私", "科研数据", "数据外发", "名单", "微信群", "外发", "敏感数据"]):
        if _is_concept(q):
            return CAT_DATA, RISK_LOW
        if _contains(q, ["发错", "误发", "泄露", "泄漏"]):
            return CAT_DATA, RISK_HIGH
        return CAT_DATA, RISK_MEDIUM

    # 3. Permission management.
    if _contains(q, ["权限", "临时权限", "外部人员", "最小权限", "审批", "越权", "访问控制"]):
        if _is_concept(q):
            return CAT_PERMISSION, RISK_LOW
        if _contains(q, ["越权", "权限异常", "被滥用", "异常权限"]):
            return CAT_PERMISSION, RISK_HIGH
        return CAT_PERMISSION, RISK_MEDIUM

    # 4. Account security.
    if _contains(q, ["被盗", "异常登录", "异地登录", "验证码", "密码泄露", "密码泄漏",
                     "密码", "多因素认证", "强密码", "找回账号", "账号", "登录异常"]):
        defensive = _contains(q, ["防止", "防范", "避免", "预防", "降低", "保护",
                                  "如何设置", "怎么设置"])
        high_hit = _contains(q, ["被盗", "异常登录", "异地登录", "密码泄露", "密码泄漏",
                                 "泄露", "泄漏", "登录异常", "验证码已", "已告诉", "已泄露", "已泄漏"])
        low_hit = _contains(q, ["强密码", "多因素认证", "密码怎么", "密码如何", "找回密码",
                                "设置密码", "什么是", "什么意思", "同一个密码", "共用"])
        if high_hit and not defensive:
            return CAT_ACCOUNT, RISK_HIGH
        if defensive or low_hit:
            return CAT_ACCOUNT, RISK_LOW
        return CAT_ACCOUNT, RISK_MEDIUM

    # 5. Terminal / device security.
    if _contains(q, ["公共WiFi", "U盘", "u盘", "电脑", "手机", "设备", "恶意软件", "病毒",
                     "丢失", "公共网络", "WiFi", "wifi"]):
        if _contains(q, ["丢失", "丢了", "掉了", "恶意软件", "病毒", "中毒", "被入侵", "被攻击"]):
            return CAT_TERMINAL, RISK_MEDIUM
        return CAT_TERMINAL, RISK_LOW

    # 6. Everything else.
    return CAT_OTHER, RISK_LOW


# ---------------------------------------------------------------------------
# Knowledge-grounded answer content
# ---------------------------------------------------------------------------

def _refusal_answer() -> dict:
    return {
        "question_type": CAT_OTHER,
        "risk_level": RISK_HIGH,
        "summary": "该问题涉及潜在违规或高风险操作，系统无法提供具体方法。",
        "reason": "该请求可能涉及未授权访问、绕过安全机制、获取他人信息或破坏系统安全，属于不应提供的攻击性、绕过性或窃取性操作内容。",
        "suggestion": (
            "如果这是正式安全测试、合规检查或课程实验需求，请通过学校或企业的授权流程申请；"
            "如果你发现系统异常、安全漏洞或账号风险，请及时联系信息中心或安全管理员。"
        ),
        "need_admin": "是",
        "refused": True,
        "raw_answer": "",
    }


def _account_answer(risk: str) -> dict:
    if risk == RISK_HIGH:
        return {
            "question_type": CAT_ACCOUNT,
            "risk_level": RISK_HIGH,
            "summary": "该问题涉及账号安全风险，需要尽快处理。",
            "reason": "账号异常、密码或验证码泄露可能导致账号被他人登录、权限被滥用或数据泄露。",
            "suggestion": (
                "①立即修改密码，避免使用生日、手机号、姓名拼音等易猜信息；"
                "②检查登录记录、绑定邮箱/手机号和多因素认证设置；"
                "③不向任何人提供密码、验证码或账号凭证；"
                "④如果涉及重要系统或敏感数据，立即联系信息中心或安全管理员冻结、核查。"
            ),
            "need_admin": "是",
            "refused": False,
            "raw_answer": "",
        }
    if risk == RISK_LOW:
        return {
            "question_type": CAT_ACCOUNT,
            "risk_level": RISK_LOW,
            "summary": "该问题属于账号安全基础知识咨询。",
            "reason": "账号安全基础知识用于帮助用户降低账号被猜测、盗用或泄露的风险。",
            "suggestion": (
                "①设置强密码：包含大小写字母、数字和符号，避免使用个人信息和连续数字；"
                "②不同系统使用不同密码，避免共用；"
                "③对重要系统、邮箱和云服务开启多因素认证；"
                "④不向他人提供密码或验证码。"
            ),
            "need_admin": "否",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_ACCOUNT,
        "risk_level": RISK_MEDIUM,
        "summary": "该问题涉及账号安全，需要注意账号凭证和登录信息的保护。",
        "reason": "账号密码、验证码等凭证一旦泄露，可能导致账号被他人登录或权限被滥用。",
        "suggestion": (
            "①避免在不可信页面或网络中输入账号密码；"
            "②定期检查登录记录和绑定信息；"
            "③不向他人提供密码、验证码；"
            "④发现异常时及时修改密码并联系信息中心或安全管理员。"
        ),
        "need_admin": "视情况而定",
        "refused": False,
        "raw_answer": "",
    }


def _phishing_answer(risk: str) -> dict:
    if risk == RISK_HIGH:
        return {
            "question_type": CAT_PHISHING,
            "risk_level": RISK_HIGH,
            "summary": "已点击链接或已提交账号信息后，需要立即采取补救措施。",
            "reason": "钓鱼邮件中的链接可能指向伪造登录页或恶意网站，已提交的账号密码或验证码可能已被攻击者获取。",
            "suggestion": (
                "①立即修改密码，并检查登录记录和绑定信息；"
                "②如果涉及支付、权限或敏感系统，尽快联系信息中心或安全管理员核查；"
                "③之后收到陌生邮件时，不点击链接、不下载附件、不扫描二维码、不填写账号密码或验证码。"
            ),
            "need_admin": "是",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_PHISHING,
        "risk_level": RISK_MEDIUM,
        "summary": "收到疑似钓鱼邮件时，不点击链接、不下载附件、不扫描二维码，也不填写账号密码或验证码。",
        "reason": "钓鱼邮件可能伪装成学校、企业或平台等可信来源，诱导用户提交账号、密码、验证码等敏感信息，导致账号被盗或信息泄露。",
        "suggestion": (
            "①不点击链接、不下载附件、不扫描二维码、不填写账号密码；"
            "②核对发件人地址和链接域名是否与官方一致；"
            "③警惕'否则封号、停用、影响权限'等制造紧张感的措辞；"
            "④通过官方网站或客服渠道核实邮件真实性；"
            "⑤无法判断时，联系信息中心或安全管理员核验；"
            "⑥如已点击或提交信息，立即修改密码并联系管理员。"
        ),
        "need_admin": "视情况而定",
        "refused": False,
        "raw_answer": "",
    }


def _data_answer(risk: str) -> dict:
    if risk == RISK_HIGH:
        return {
            "question_type": CAT_DATA,
            "risk_level": RISK_HIGH,
            "summary": "敏感数据已误发或泄露时，需要尽快控制影响范围并上报。",
            "reason": "包含个人信息的文件误发到群聊或外部渠道后，可能造成个人信息或内部数据泄露。",
            "suggestion": (
                "①尽快联系群管理员或接收方删除相关内容；"
                "②立即联系信息中心或安全管理员评估影响范围；"
                "③涉及个人信息时评估是否需要脱敏或采取补救措施；"
                "④后续避免通过公开网盘、社交群聊等不受控渠道传输敏感数据。"
            ),
            "need_admin": "是",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_DATA,
        "risk_level": RISK_MEDIUM,
        "summary": "该问题涉及数据安全或个人信息处理，需要谨慎判断。",
        "reason": "个人信息、学生信息和科研数据在共享、传输和存储过程中可能产生泄露风险。",
        "suggestion": (
            "①遵循必要、最小原则，只收集必要数据；"
            "②确认接收对象、使用目的和保存方式是否合理；"
            "③避免通过公开网盘、社交群聊等不受控渠道传输敏感数据；"
            "④涉及个人信息时先做脱敏处理；"
            "⑤重要数据优先使用学校或企业指定系统存储；"
            "⑥发生误发、泄露或异常访问时及时联系信息中心或安全管理员。"
        ),
        "need_admin": "视情况而定",
        "refused": False,
        "raw_answer": "",
    }


def _permission_answer(risk: str) -> dict:
    if risk == RISK_HIGH:
        return {
            "question_type": CAT_PERMISSION,
            "risk_level": RISK_HIGH,
            "summary": "权限异常或越权访问需要立即核查和处理。",
            "reason": "权限被滥用、越权访问或拥有不应有的权限，可能导致敏感数据或系统被未授权访问。",
            "suggestion": (
                "①停止使用异常权限进行任何操作；"
                "②立即联系系统管理员或信息中心核查权限来源和影响范围；"
                "③配合管理员回收或修正权限，并遵循最小权限原则重新授权。"
            ),
            "need_admin": "是",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_PERMISSION,
        "risk_level": RISK_MEDIUM,
        "summary": "该问题涉及系统权限申请或访问控制，应遵循正式审批流程和最小权限原则。",
        "reason": "权限过大、长期保留或外部人员访问不规范，可能导致越权访问和数据泄露。",
        "suggestion": (
            "①说明申请原因、使用场景、所需权限范围、使用期限和审批人；"
            "②遵循最小权限原则，只申请完成工作所需的最低权限；"
            "③通过学校或企业指定流程提交，不通过口头、私聊等非正式方式授权；"
            "④临时权限设置明确有效期，用后及时回收；"
            "⑤外部人员访问需正式审批并明确范围和责任人；"
            "⑥发现权限异常或越权时及时联系系统管理员。"
        ),
        "need_admin": "视情况而定",
        "refused": False,
        "raw_answer": "",
    }


def _terminal_answer(risk: str) -> dict:
    if risk == RISK_MEDIUM:
        return {
            "question_type": CAT_TERMINAL,
            "risk_level": RISK_MEDIUM,
            "summary": "设备丢失或发现恶意软件/病毒时，需要尽快处理以降低账号和数据风险。",
            "reason": "设备丢失、中毒或存在恶意软件时，账号凭证和数据可能面临被他人访问或窃取的风险。",
            "suggestion": (
                "①尽快修改密码；"
                "②检查登录记录；"
                "③对中毒设备进行查杀或重装，不运行来路不明的软件；"
                "④必要时联系信息中心或安全管理员处理。"
            ),
            "need_admin": "视情况而定",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_TERMINAL,
        "risk_level": RISK_LOW,
        "summary": "该问题属于终端安全或设备使用风险咨询。",
        "reason": "公共网络、未知 U 盘、异常软件或设备使用不当都可能带来账号和数据风险。",
        "suggestion": (
            "①避免连接不可信的公共WiFi处理敏感操作；"
            "②不插入来源不明的U盘，不使用未知设备；"
            "③不安装来路不明的软件，避免访问可疑网站；"
            "④设备丢失或发现异常时及时联系信息中心或安全管理员。"
        ),
        "need_admin": "否",
        "refused": False,
        "raw_answer": "",
    }


def _other_answer() -> dict:
    return {
        "question_type": CAT_OTHER,
        "risk_level": RISK_LOW,
        "summary": "当前问题属于一般安全咨询。",
        "reason": "根据当前输入，系统未识别到明确的账号、权限、数据或高风险安全事件。",
        "suggestion": (
            "请补充具体场景，例如是否涉及账号异常、可疑邮件、数据外发、权限申请或设备异常；"
            "如果问题涉及具体安全事件，建议联系信息中心或安全管理员。"
        ),
        "need_admin": "否",
        "refused": False,
        "raw_answer": "",
    }


def _concept_answer(category: str) -> dict:
    """Answer a definition / concept question with a knowledge-base definition."""
    if category == CAT_PHISHING:
        return {
            "question_type": CAT_PHISHING,
            "risk_level": RISK_LOW,
            "summary": "钓鱼邮件是指伪装成学校、企业、平台、银行等可信来源，诱导用户点击链接、下载附件、填写账号密码或提供验证码的邮件。",
            "reason": "钓鱼邮件可能导致账号被盗、敏感信息泄露、恶意软件感染或权限被滥用。",
            "suggestion": (
                "识别钓鱼邮件时注意：①核对发件人地址和链接域名是否与官方一致；"
                "②警惕'否则封号、停用'等制造紧张感的措辞；"
                "③不点击链接、不下载附件、不填写账号密码和验证码。"
            ),
            "need_admin": "否",
            "refused": False,
            "raw_answer": "",
        }
    if category == CAT_DATA:
        return {
            "question_type": CAT_DATA,
            "risk_level": RISK_LOW,
            "summary": "敏感数据包括个人身份信息、学生信息、联系方式、身份证号、账号凭证、科研数据、业务数据等。",
            "reason": "敏感数据一旦在传输或存储过程中失控，可能造成个人信息或内部数据泄露。",
            "suggestion": (
                "处理敏感数据时遵循必要、最小原则，只收集必要数据；"
                "避免通过公开网盘、社交群聊等不受控渠道传输；必要时先做脱敏处理。"
            ),
            "need_admin": "否",
            "refused": False,
            "raw_answer": "",
        }
    if category == CAT_PERMISSION:
        return {
            "question_type": CAT_PERMISSION,
            "risk_level": RISK_LOW,
            "summary": "最小权限原则是指用户只应拥有完成当前工作所必需的最低权限，不应长期持有与工作无关或超出职责范围的权限。",
            "reason": "最小权限可以降低账号被盗、误操作、越权访问和数据泄露的风险。",
            "suggestion": (
                "申请权限时说明申请原因和范围，遵循最小权限原则；"
                "通过指定流程审批；临时权限设置明确有效期并及时回收。"
            ),
            "need_admin": "否",
            "refused": False,
            "raw_answer": "",
        }
    return {
        "question_type": CAT_ACCOUNT,
        "risk_level": RISK_LOW,
        "summary": "多因素认证是指除密码之外，再增加短信验证码、动态口令、认证App、硬件密钥等额外验证方式，可以降低单一密码泄露带来的风险。",
        "reason": "账号安全基础知识用于帮助用户降低账号被猜测、盗用或泄露的风险。",
        "suggestion": (
            "①设置强密码：包含大小写字母、数字和符号，避免使用个人信息和连续数字；"
            "②不同系统使用不同密码，避免共用；"
            "③对重要系统、邮箱和云服务开启多因素认证；"
            "④不向他人提供密码或验证码。"
        ),
        "need_admin": "否",
        "refused": False,
        "raw_answer": "",
    }


def build_answer(question: str) -> dict:
    """Build a full structured answer dict for a question."""
    category, risk = classify(question)

    if _is_refusal(question):
        return _refusal_answer()
    if _is_concept(question) and category != CAT_OTHER:
        return _concept_answer(category)
    if category == CAT_ACCOUNT:
        return _account_answer(risk)
    if category == CAT_PHISHING:
        return _phishing_answer(risk)
    if category == CAT_DATA:
        return _data_answer(risk)
    if category == CAT_PERMISSION:
        return _permission_answer(risk)
    if category == CAT_TERMINAL:
        return _terminal_answer(risk)
    return _other_answer()


def get_mock_answer(question: str) -> dict:
    """Public entry point for the local mock engine."""
    return build_answer(question)


# ---------------------------------------------------------------------------
# Dify answer parsing
# ---------------------------------------------------------------------------

_FIELD_MAP = {
    "问题类型": "question_type",
    "风险等级": "risk_level",
    "简要结论": "summary",
    "原因说明": "reason",
    "建议操作": "suggestion",
    "是否需要联系管理员": "need_admin",
}


def parse_dify_answer(answer: str) -> dict:
    """Parse a structured Dify answer into a dict.

    Handles Chinese/English colons, markdown bold labels, multi-line values and
    risk-level normalization. Keeps the raw answer for later Bad Case analysis.
    """
    result = {
        "question_type": "未解析",
        "risk_level": "未解析",
        "summary": "",
        "reason": "",
        "suggestion": "",
        "need_admin": "",
        "refused": False,
        "raw_answer": answer or "",
    }

    # Normalize each line: strip markdown bold/headings and trailing punctuation.
    # Dify frequently answers with "**问题类型**：xxx", so the asterisks inside
    # the label must be removed before prefix matching, not only at the edges.
    lines = [
        ln.strip().lstrip("#").replace("**", "").lstrip("*").strip()
        for ln in (answer or "").splitlines()
    ]
    current_key = None

    for line in lines:
        if not line:
            continue
        matched = False
        for label, key in _FIELD_MAP.items():
            # Match a label at the start of a line, allowing optional markdown/bold.
            clean = line.lstrip("*").lstrip()
            if clean.startswith(label):
                value = clean[len(label):].lstrip("：: ").strip()
                result[key] = value
                current_key = key
                matched = True
                break
        if not matched and current_key:
            sep = "\n" if result[current_key] else ""
            result[current_key] = result[current_key] + sep + line

    if not result["summary"]:
        result["summary"] = (answer or "")[:300]

    result["risk_level"] = normalize_risk(result["risk_level"])
    # A refusal answer is one whose risk is 高 and whose type/other indicates refusal.
    if result["risk_level"] == RISK_HIGH and (
        "无法提供" in result["summary"] or "拒绝" in result["summary"] or "违规" in result["summary"]
    ):
        result["refused"] = True

    return result


def answer_full_text(answer: dict) -> str:
    """Concatenate the visible answer fields for coverage checks."""
    parts = [
        answer.get("question_type", ""),
        answer.get("risk_level", ""),
        answer.get("summary", ""),
        answer.get("reason", ""),
        answer.get("suggestion", ""),
        answer.get("need_admin", ""),
    ]
    return "\n".join(str(p) for p in parts if p)

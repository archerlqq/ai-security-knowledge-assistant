import csv
from datetime import datetime
from pathlib import Path

# 锚定到项目根目录，而不是当前工作目录：
# 否则从其他目录启动 Streamlit 时，会在错误的位置创建 data/ 并写丢反馈。
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.csv"

FIELDNAMES = [
    "timestamp",
    "question",
    "answer",
    "question_type",
    "risk_level",
    "feedback"
]

def ensure_feedback_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_FILE.exists():
        with FEEDBACK_FILE.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def save_feedback(question, answer, question_type, risk_level, feedback):
    ensure_feedback_file()
    with FEEDBACK_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "answer": answer,
            "question_type": question_type,
            "risk_level": risk_level,
            "feedback": feedback
        })
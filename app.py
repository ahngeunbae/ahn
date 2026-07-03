import html
import json
import time
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "todos.json"

CATEGORIES = ["업무", "개인", "공부"]
FILTER_OPTIONS = ["전체"] + CATEGORIES
AUTO_OPTION = "🔍 자동 분류"

CATEGORY_COLORS = {
    "업무": ("#dfeaff", "#3466c4"),
    "개인": ("#ffe1ec", "#cf5b85"),
    "공부": ("#dff5e3", "#379154"),
}

CATEGORY_KEYWORDS = {
    "업무": [
        "회의", "미팅", "보고서", "프로젝트", "업무", "메일", "이메일", "발표",
        "출장", "계약", "클라이언트", "고객", "회사", "야근", "결재", "기획",
        "협업", "마감", "제출", "회의록", "팀", "업체", "영업", "품의",
    ],
    "개인": [
        "운동", "헬스", "병원", "쇼핑", "여행", "가족", "친구", "취미", "청소",
        "빨래", "약속", "생일", "휴식", "산책", "장보기", "요리", "반려동물",
        "은행", "택배", "차량", "정비", "데이트",
    ],
    "공부": [
        "공부", "시험", "숙제", "과제", "강의", "책", "독서", "복습", "예습",
        "학습", "논문", "자격증", "토익", "코딩", "스터디", "수업", "강좌",
        "문제집", "암기", "리포트",
    ],
}


def classify_category(text):
    lowered = text.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lowered:
                scores[cat] += 1

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "개인", False
    return best_cat, True


def load_todos():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(todos, text, category):
    todos.append(
        {
            "id": time.time_ns(),
            "text": text,
            "category": category,
            "completed": False,
        }
    )
    save_todos(todos)


def toggle_todo(todos, todo_id):
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = not todo["completed"]
            break
    save_todos(todos)


def delete_todo(todos, todo_id):
    todos[:] = [t for t in todos if t["id"] != todo_id]
    save_todos(todos)


def save_edit(todos, todo_id, new_text):
    new_text = new_text.strip()
    if not new_text:
        return
    for todo in todos:
        if todo["id"] == todo_id:
            todo["text"] = new_text
            break
    save_todos(todos)


st.set_page_config(page_title="오늘의 할 일", page_icon="📝", layout="centered")

if "filter" not in st.session_state:
    st.session_state.filter = "전체"
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 8%, rgba(99, 102, 241, 0.08), transparent 45%),
            radial-gradient(circle at 88% 92%, rgba(236, 72, 153, 0.06), transparent 45%),
            #eef1f8;
    }
    .block-container {
        max-width: 560px;
        padding-top: 2.5rem;
        padding-bottom: 2rem;
    }
    .app-title {
        text-align: center;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 1.2rem;
    }
    .progress-box {
        background: linear-gradient(135deg, #eef0fe, #f7f8ff);
        padding: 16px 18px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .progress-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        font-weight: 600;
        color: #9198a9;
        margin-bottom: 10px;
    }
    .progress-percent {
        font-weight: 800;
        color: #6366f1;
        font-size: 1rem;
    }
    .progress-track {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(99, 102, 241, 0.12);
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #818cf8, #6366f1);
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.45);
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .todo-tag {
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        white-space: nowrap;
    }
    .todo-text {
        font-size: 0.92rem;
    }
    .todo-text.completed {
        color: #9198a9;
        text-decoration: line-through;
    }
    .empty-message {
        text-align: center;
        color: #9198a9;
        font-size: 0.85rem;
        padding: 40px 0 30px;
    }
    .footer-note {
        text-align: center;
        font-size: 0.74rem;
        line-height: 1.6;
        color: #a7adba;
        margin-top: 1.8rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(145, 152, 169, 0.18);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        margin-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

todos = load_todos()

st.markdown('<h1 class="app-title">📝 오늘의 할 일</h1>', unsafe_allow_html=True)

# ── 진행률 (현재 필터 기준) ──────────────────────────
if st.session_state.filter == "전체":
    filtered_for_progress = todos
else:
    filtered_for_progress = [t for t in todos if t["category"] == st.session_state.filter]

total = len(filtered_for_progress)
completed_count = len([t for t in filtered_for_progress if t["completed"]])
percent = round((completed_count / total) * 100) if total else 0

st.markdown(
    f"""
    <div class="progress-box">
        <div class="progress-header">
            <span>진행률</span>
            <span class="progress-percent">{percent}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{percent}%;"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 할 일 추가 ──────────────────────────
with st.form("add_form", clear_on_submit=True):
    col_category, col_text, col_btn = st.columns([1.3, 2.3, 1])
    category = col_category.selectbox(
        "카테고리", [AUTO_OPTION] + CATEGORIES, label_visibility="collapsed"
    )
    text = col_text.text_input(
        "할 일", placeholder="할 일을 입력하세요", label_visibility="collapsed"
    )
    submitted = col_btn.form_submit_button("추가", use_container_width=True)
    if submitted and text.strip():
        clean_text = text.strip()
        if category == AUTO_OPTION:
            final_category, matched = classify_category(clean_text)
            add_todo(todos, clean_text, final_category)
            if matched:
                st.toast(f"🔍 '{clean_text}' → [{final_category}]로 자동 분류되었습니다.")
            else:
                st.toast(f"🔍 일치하는 키워드가 없어 [{final_category}]로 분류되었습니다.")
        else:
            add_todo(todos, clean_text, category)
        st.rerun()

# ── 카테고리 필터 탭 ──────────────────────────
filter_cols = st.columns(len(FILTER_OPTIONS))
for col, option in zip(filter_cols, FILTER_OPTIONS):
    is_active = st.session_state.filter == option
    if col.button(
        option,
        key=f"filter_{option}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        st.session_state.filter = option
        st.rerun()

# ── 할 일 목록 ──────────────────────────
if st.session_state.filter == "전체":
    filtered_todos = todos
else:
    filtered_todos = [t for t in todos if t["category"] == st.session_state.filter]

if not filtered_todos:
    st.markdown(
        '<div class="empty-message">🗒️<br>할 일이 없습니다.</div>',
        unsafe_allow_html=True,
    )

for todo in filtered_todos:
    tid = todo["id"]

    with st.container(border=True):
        if st.session_state.editing_id == tid:
            col_input, col_save = st.columns([4, 1])
            new_text = col_input.text_input(
                "수정",
                value=todo["text"],
                key=f"edit_input_{tid}",
                label_visibility="collapsed",
            )
            if col_save.button("✓ 저장", key=f"save_{tid}", use_container_width=True):
                save_edit(todos, tid, new_text)
                st.session_state.editing_id = None
                del st.session_state[f"edit_input_{tid}"]
                st.rerun()
        else:
            col_check, col_tag, col_text, col_edit, col_delete = st.columns(
                [0.5, 1, 3.2, 0.5, 0.5]
            )

            checked = col_check.checkbox(
                "완료",
                value=todo["completed"],
                key=f"chk_{tid}",
                label_visibility="collapsed",
            )
            if checked != todo["completed"]:
                toggle_todo(todos, tid)
                st.rerun()

            bg, fg = CATEGORY_COLORS[todo["category"]]
            col_tag.markdown(
                f'<span class="todo-tag" style="background:{bg};color:{fg};">{todo["category"]}</span>',
                unsafe_allow_html=True,
            )

            text_class = "todo-text completed" if todo["completed"] else "todo-text"
            col_text.markdown(
                f'<span class="{text_class}">{html.escape(todo["text"])}</span>',
                unsafe_allow_html=True,
            )

            if col_edit.button("✎", key=f"editbtn_{tid}", help="수정"):
                st.session_state.editing_id = tid
                st.rerun()

            if col_delete.button("✕", key=f"delbtn_{tid}", help="삭제"):
                delete_todo(todos, tid)
                st.rerun()

# ── 안내 문구 ──────────────────────────
st.markdown(
    '<div class="footer-note">ℹ️ 본 앱은 로컬 파일(todos.json)에 데이터를 저장하므로, '
    "해당 파일을 삭제하면 데이터가 초기화될 수 있습니다.</div>",
    unsafe_allow_html=True,
)

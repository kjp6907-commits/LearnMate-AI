import base64
import os
from pathlib import Path
import streamlit as st

from gemini_service import (
    DEFAULT_MODEL,
    GeminiServiceError,
    generate_chat_response,
    generate_quiz_question,
    is_api_configured,
)
from prompts import get_tutor_system_prompt

# Page configuration
st.set_page_config(
    page_title="LearnMate AI - Personalized Learning Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Robust path resolution for mascot asset (works both locally and on Streamlit Cloud)
BASE_DIR = Path(__file__).resolve().parent
MASCOT_PATH = BASE_DIR / "assets" / "mascot.jpg"

def get_mascot_base64():
    if MASCOT_PATH.exists():
        with open(MASCOT_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

mascot_b64 = get_mascot_base64()
mascot_src = f"data:image/jpeg;base64,{mascot_b64}" if mascot_b64 else ""

# ----------------- CUSTOM CSS: DRIBBLE "QUIZY." GLASSMORPHIC THEME -----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global App Background: Cosmic Berry & Deep Twilight Gradient */
    .stApp {
        background: radial-gradient(circle at 12% 18%, rgba(214, 40, 89, 0.38) 0%, transparent 45%),
                    radial-gradient(circle at 85% 22%, rgba(130, 48, 200, 0.45) 0%, transparent 50%),
                    radial-gradient(circle at 50% 88%, rgba(40, 15, 75, 0.7) 0%, transparent 55%),
                    #090312 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        color: #f6f7fb !important;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 6, 27, 0.85) !important;
        backdrop-filter: blur(28px) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Glass Cards */
    .quizy-hero-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 28px;
        padding: 32px 36px;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .quizy-hero-card::before {
        content: '';
        position: absolute;
        top: -40%;
        right: -20%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(255, 75, 110, 0.3) 0%, transparent 70%);
        pointer-events: none;
    }

    /* Top Brand Bar */
    .brand-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .brand-title {
        font-family: 'Outfit', sans-serif;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 0.5px;
        color: #ffffff;
        text-transform: uppercase;
    }
    .brand-title span {
        color: #ff476f;
    }
    .brand-pill {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #ffd6df;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 9999px;
        backdrop-filter: blur(10px);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Bold Dribbble Hero Typography */
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 40px;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.8px;
        color: #ffffff;
        margin: 0 0 14px 0;
    }
    .hero-subtitle {
        font-size: 16px;
        line-height: 1.55;
        color: rgba(255, 255, 255, 0.75);
        margin: 0 0 22px 0;
        max-width: 600px;
    }

    /* Feature Badges */
    .badge-group {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
    }
    .feature-badge {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 600;
        color: #f1f3f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 3D Floating Mascot Avatar */
    .mascot-container {
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
    }
    .mascot-img {
        width: 220px;
        height: 220px;
        object-fit: cover;
        border-radius: 28px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 40px rgba(255, 75, 110, 0.35);
        border: 2px solid rgba(255, 255, 255, 0.2);
        animation: floatAnimation 4s ease-in-out infinite;
    }

    @keyframes floatAnimation {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }

    /* Streamlit Chat Bubbles Glassmorphic */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 22px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3) !important;
        padding: 16px 22px !important;
        margin-bottom: 16px !important;
    }

    /* Streamlit Pill Buttons */
    .stButton > button {
        border-radius: 9999px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        letter-spacing: 0.2px !important;
        transition: all 0.22s ease-in-out !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff4365 0%, #ff758c 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 8px 24px rgba(255, 67, 101, 0.45) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(255, 67, 101, 0.65) !important;
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        backdrop-filter: blur(12px) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* Quiz Radio Choices Styled as Sleek Glass Cards */
    div[data-testid="stRadio"] > div {
        gap: 12px !important;
    }
    div[data-testid="stRadio"] label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 18px !important;
        padding: 14px 20px !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        backdrop-filter: blur(12px) !important;
        width: 100% !important;
    }
    div[data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: #ff4365 !important;
        box-shadow: 0 6px 20px rgba(255, 67, 101, 0.25) !important;
        transform: translateX(4px) !important;
    }

    /* Pinned Bottom Chat Input */
    [data-testid="stChatInput"] {
        border-radius: 9999px !important;
        background: rgba(20, 7, 36, 0.85) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(24px) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #ff4365 !important;
        box-shadow: 0 0 25px rgba(255, 67, 101, 0.45) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initial welcome message for normal tutoring
DEFAULT_GREETING = {
    "role": "assistant",
    "content": (
        "Hello! 👋 I am **LearnMate AI**, your personalized learning tutor. "
        "What academic topic, concept, or homework problem would you like to explore today?"
    ),
}

# ----------------- SESSION STATE INITIALIZATION -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [DEFAULT_GREETING]

if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = None
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_total" not in st.session_state:
    st.session_state.quiz_total = 0
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
if "quiz_current_q" not in st.session_state:
    st.session_state.quiz_current_q = None
if "quiz_answered" not in st.session_state:
    st.session_state.quiz_answered = False
if "quiz_last_choice" not in st.session_state:
    st.session_state.quiz_last_choice = None
if "quiz_finished" not in st.session_state:
    st.session_state.quiz_finished = False
if "quiz_previous_questions" not in st.session_state:
    st.session_state.quiz_previous_questions = []


def reset_quiz(keep_topic: bool = False):
    """Resets quiz progress while optionally retaining the current topic."""
    st.session_state.quiz_score = 0
    st.session_state.quiz_total = 0
    st.session_state.quiz_history = []
    st.session_state.quiz_current_q = None
    st.session_state.quiz_answered = False
    st.session_state.quiz_last_choice = None
    st.session_state.quiz_finished = False
    st.session_state.quiz_previous_questions = []
    if not keep_topic:
        st.session_state.quiz_topic = None


# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-family: 'Outfit'; font-size: 22px; font-weight: 900; color: #fff;">
                LEARNMATE<span style="color: #ff476f;">.</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Empowering learners worldwide (SDG 4: Quality Education)")

    st.markdown("---")

    # Quiz Mode Toggle
    quiz_mode = st.toggle(
        "🎯 Quiz Mode",
        value=False,
        help="Toggle between free-form tutoring and interactive practice quizzes.",
    )

    st.markdown("---")

    # Learner Level selection
    learner_level = st.selectbox(
        "📚 Target Learner Level:",
        [
            "Beginner (Everyday language & simple analogies)",
            "Intermediate (Balanced explanations & practical depth)",
            "Advanced (Technical rigor, formulas & precision)",
        ],
        index=0,
        help="Adjusts how LearnMate tailors explanations and vocabulary.",
    )

    st.markdown("---")

    # Dynamic sidebar options based on Mode
    if not quiz_mode:
        if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
            st.session_state.messages = [DEFAULT_GREETING]
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            **💡 Quick Topic Ideas:**
            - *"Explain photosynthesis using a kitchen analogy"*
            - *"How does binary search work step-by-step?"*
            - *"Why does gravity cause objects to orbit?"*
            - *"Help me understand supply and demand curves"*
            """
        )
    else:
        st.subheader("🎯 Quiz Dashboard")
        if st.session_state.quiz_topic:
            st.markdown(f"**Topic:** `{st.session_state.quiz_topic}`")
            st.markdown(
                f"**Current Score:** `{st.session_state.quiz_score} / {st.session_state.quiz_total}`"
            )

            if st.session_state.quiz_total > 0 and not st.session_state.quiz_finished:
                if st.button("📊 View Performance Summary", use_container_width=True):
                    st.session_state.quiz_finished = True
                    st.rerun()

            if st.button("🔄 Change Topic", use_container_width=True):
                reset_quiz(keep_topic=False)
                st.rerun()

            if st.button("🔁 Reset Score", use_container_width=True):
                reset_quiz(keep_topic=True)
                st.rerun()
        else:
            st.info("Choose a topic in the main view to start practicing.")

    # API Configuration Status
    st.markdown("---")
    if is_api_configured():
        st.success("✅ Gemini AI Connected")
    else:
        st.warning("⚠️ `GEMINI_API_KEY` missing")
        with st.expander("🔑 Paste API Key Here", expanded=True):
            st.caption("Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey)")
            user_entered_key = st.text_input(
                "Gemini API Key:",
                type="password",
                placeholder="AIzaSy...",
                label_visibility="collapsed",
            )
            if st.button("Save & Connect 🚀", use_container_width=True, type="primary"):
                clean_key = user_entered_key.strip()
                if clean_key:
                    os.environ["GEMINI_API_KEY"] = clean_key
                    st.session_state["gemini_api_key"] = clean_key
                    try:
                        with open(".env", "w", encoding="utf-8") as env_f:
                            env_f.write(
                                f"# LearnMate AI - Local Environment Variables\n"
                                f"GEMINI_API_KEY={clean_key}\n"
                            )
                    except Exception:
                        pass
                    st.success("Connected successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid key.")

    st.caption(f"Engine: `{DEFAULT_MODEL}`")


# ----------------- MAIN UI -----------------
if not quiz_mode:
    # ==========================================
    # MODE 1: NORMAL TUTORING CONVERSATION
    # ==========================================

    # Custom Dribbble-style Hero Card with 3D Mascot
    hero_cols = st.columns([3, 2])
    with hero_cols[0]:
        st.markdown(
            f"""
            <div class="quizy-hero-card">
                <div class="brand-bar">
                    <div class="brand-title">LEARNMATE<span>.</span></div>
                    <div class="brand-pill">🎯 SDG 4 Quality Education</div>
                </div>
                <div class="hero-title">Ready To Boost Your Knowledge With Smart AI Learning?</div>
                <div class="hero-subtitle">
                    Your personal AI tutor. Ask any question, break complex concepts into intuitive analogies, and master topics step-by-step.
                </div>
                <div class="badge-group">
                    <div class="feature-badge">⚡ Instant Simple Explanations</div>
                    <div class="feature-badge">🧩 Real-World Analogies</div>
                    <div class="feature-badge">❓ Check Questions</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_cols[1]:
        if mascot_src:
            st.markdown(
                f"""
                <div class="mascot-container" style="height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{mascot_src}" class="mascot-img" alt="LearnMate AI Mascot" />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🤖 LearnMate AI Tutor")

    # Render all previous chat messages with mascot avatar
    for msg in st.session_state.messages:
        avatar = str(MASCOT_PATH) if msg["role"] == "assistant" and MASCOT_PATH.exists() else ("🎓" if msg["role"] == "user" else None)
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # User Chat Input
    if user_prompt := st.chat_input("Ask a question, paste a problem, or request an explanation..."):
        clean_prompt = user_prompt.strip()
        if not clean_prompt:
            st.warning("Please enter a question or topic before submitting.")
            st.stop()

        if len(clean_prompt) > 10000:
            st.warning("Your message is longer than 10,000 characters. Please break your question into smaller parts.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": clean_prompt})
        with st.chat_message("user", avatar="🎓"):
            st.markdown(clean_prompt)

        if not is_api_configured():
            with st.chat_message("assistant", avatar="assets/mascot.jpg" if Path("assets/mascot.jpg").exists() else None):
                warning_msg = (
                    "⚠️ **Gemini API key is not configured.** "
                    "Please add your `GEMINI_API_KEY` to the `.env` file and restart the app."
                )
                st.error(warning_msg)
                st.session_state.messages.append({"role": "assistant", "content": warning_msg})
        else:
            with st.chat_message("assistant", avatar="assets/mascot.jpg" if Path("assets/mascot.jpg").exists() else None):
                system_instruction = get_tutor_system_prompt(learner_level=learner_level)

                with st.spinner("LearnMate is thinking..."):
                    try:
                        bot_response = generate_chat_response(
                            messages=st.session_state.messages,
                            system_instruction=system_instruction,
                            model=DEFAULT_MODEL,
                        )
                        st.markdown(bot_response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": bot_response}
                        )
                    except GeminiServiceError as err:
                        error_feedback = f"⚠️ **Tutor Service Notice**: {err}"
                        st.error(error_feedback)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_feedback}
                        )
                    except Exception:
                        generic_feedback = (
                            "⚠️ **An unexpected error occurred while generating the response.** "
                            "Please try again."
                        )
                        st.error(generic_feedback)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": generic_feedback}
                        )

else:
    # ==========================================
    # MODE 2: INTERACTIVE QUIZ MODE ("QUIZY." STYLE)
    # ==========================================
    quiz_hero_cols = st.columns([3, 2])
    with quiz_hero_cols[0]:
        st.markdown(
            f"""
            <div class="quizy-hero-card">
                <div class="brand-bar">
                    <div class="brand-title">QUIZ<span>.</span>MODE</div>
                    <div class="brand-pill">⚡ Active Recall Assessment</div>
                </div>
                <div class="hero-title">Ready To Boost Your Grades With Smart AI Tests?</div>
                <div class="hero-subtitle">
                    Test your understanding with adaptive multiple-choice questions. Get instant constructive feedback and master any topic.
                </div>
                <div class="badge-group">
                    <div class="feature-badge">🎯 Adaptive MCQs</div>
                    <div class="feature-badge">💡 Instant Explanations</div>
                    <div class="feature-badge">📈 Live Score Tracking</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with quiz_hero_cols[1]:
        if mascot_src:
            st.markdown(
                f"""
                <div class="mascot-container" style="height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{mascot_src}" class="mascot-img" alt="Quiz Robot" />
                </div>
                """,
                unsafe_allow_html=True,
            )

    if not is_api_configured():
        st.error(
            "⚠️ **Gemini API key is missing.** Please configure `GEMINI_API_KEY` in `.env` to start quiz practice."
        )

    # 1. Performance Summary Screen
    elif st.session_state.quiz_finished:
        st.markdown("## 📊 Quiz Performance Summary")
        score = st.session_state.quiz_score
        total = st.session_state.quiz_total
        pct = (score / total * 100) if total > 0 else 0

        # Score Banner
        col1, col2, col3 = st.columns(3)
        col1.metric("Questions Attempted", total)
        col2.metric("Correct Answers", f"{score} / {total}")
        col3.metric("Accuracy Rate", f"{pct:.1f}%")

        if pct >= 80:
            st.success(
                f"🌟 **Outstanding Mastery!** You scored **{score}/{total} ({pct:.0f}%)** on **{st.session_state.quiz_topic}**. "
                "You have a solid grasp of these concepts!"
            )
        elif pct >= 50:
            st.info(
                f"👍 **Good Progress!** You scored **{score}/{total} ({pct:.0f}%)** on **{st.session_state.quiz_topic}**. "
                "Review the feedback below to strengthen the few concepts you missed."
            )
        else:
            st.warning(
                f"🌱 **Keep Practicing!** You scored **{score}/{total} ({pct:.0f}%)** on **{st.session_state.quiz_topic}**. "
                "Learning takes patience. Read through the explanations below or switch back to Chat Mode to ask LearnMate for simpler analogies!"
            )

        st.markdown("---")
        st.subheader("📝 Question Breakdown")

        for idx, item in enumerate(st.session_state.quiz_history, 1):
            status_icon = "✅" if item["is_correct"] else "❌"
            with st.expander(f"{status_icon} Question {idx}: {item['question']}", expanded=(idx == 1)):
                st.write(f"**Your Choice:** ({item['selected']}) {item['options'].get(item['selected'], '')}")
                st.write(f"**Correct Answer:** ({item['correct']}) {item['options'].get(item['correct'], '')}")
                st.info(f"**💡 Explanation:** {item['explanation']}")

        st.markdown("---")
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("🔄 Practice More on this Topic", use_container_width=True, type="primary"):
                reset_quiz(keep_topic=True)
                st.rerun()
        with btn_c2:
            if st.button("📚 Practice a Different Topic", use_container_width=True):
                reset_quiz(keep_topic=False)
                st.rerun()

    # 2. Topic Selection Screen (if no topic is known)
    elif not st.session_state.quiz_topic:
        st.markdown("### 📚 What topic would you like to practice?")
        st.write(
            "Enter any subject or concept. LearnMate will generate one MCQ at a time, "
            f"adapted to your chosen **{learner_level.split(' ')[0]}** level."
        )

        topic_input = st.text_input(
            "Enter practice topic:",
            placeholder="e.g., Photosynthesis, Newton's Laws of Motion, Fractions & Decimals, Cell Division...",
        )

        st.write("Or pick a popular topic to test instantly:")
        col1, col2, col3, col4 = st.columns(4)
        quick_topic = None
        if col1.button("🌱 Photosynthesis", use_container_width=True):
            quick_topic = "Photosynthesis"
        if col2.button("🍎 Newton's Laws", use_container_width=True):
            quick_topic = "Newton's Laws of Motion"
        if col3.button("🔢 Fractions & Ratios", use_container_width=True):
            quick_topic = "Fractions and Ratios"
        if col4.button("🐍 Python Functions", use_container_width=True):
            quick_topic = "Python Functions and Scope"

        selected_topic = quick_topic or topic_input

        if st.button("Start Quiz 🚀", type="primary", use_container_width=True) or quick_topic:
            if selected_topic and selected_topic.strip():
                reset_quiz(keep_topic=False)
                st.session_state.quiz_topic = selected_topic.strip()
                st.rerun()
            else:
                st.warning("Please type or select a topic to begin.")

    # 3. Active Quiz Question Screen
    else:
        # Live Score Banner
        header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
        with header_col1:
            st.markdown(f"**Topic:** `{st.session_state.quiz_topic}` | **Level:** `{learner_level.split(' ')[0]}`")
        with header_col2:
            st.metric("Running Score", f"{st.session_state.quiz_score} / {st.session_state.quiz_total}")
        with header_col3:
            curr_pct = (
                f"{(st.session_state.quiz_score / st.session_state.quiz_total * 100):.0f}%"
                if st.session_state.quiz_total > 0
                else "N/A"
            )
            st.metric("Accuracy", curr_pct)

        st.markdown("---")

        # Generate next question if not already in session state
        if st.session_state.quiz_current_q is None:
            level_tag = learner_level.split(" ")[0]
            with st.spinner(f"Preparing question {st.session_state.quiz_total + 1} on '{st.session_state.quiz_topic}'..."):
                try:
                    q_data = generate_quiz_question(
                        topic=st.session_state.quiz_topic,
                        learner_level=level_tag,
                        previous_questions=st.session_state.quiz_previous_questions,
                    )
                    st.session_state.quiz_current_q = q_data
                    st.session_state.quiz_previous_questions.append(q_data["question"])
                    st.session_state.quiz_answered = False
                    st.session_state.quiz_last_choice = None
                    st.rerun()
                except GeminiServiceError as err:
                    st.error(f"Error generating question: {err}")
                    if st.button("Try Again 🔄"):
                        st.rerun()
                    st.stop()

        q = st.session_state.quiz_current_q

        # A. Waiting for student's answer (DO NOT REVEAL CORRECT ANSWER)
        if not st.session_state.quiz_answered:
            st.markdown(f"### Question {st.session_state.quiz_total + 1}")
            st.markdown(f"#### ❓ {q['question']}")

            st.write("Choose your answer:")
            with st.form("quiz_form"):
                choice = st.radio(
                    label="Options:",
                    options=["A", "B", "C", "D"],
                    format_func=lambda opt: f"**({opt})** {q['options'].get(opt, '')}",
                    index=None,
                    label_visibility="collapsed",
                )
                submit = st.form_submit_button("Submit Answer ✍️", type="primary", use_container_width=True)

                if submit:
                    if not choice:
                        st.warning("Please select an option before submitting.")
                    else:
                        is_correct = (choice == q["correct_option"])
                        st.session_state.quiz_answered = True
                        st.session_state.quiz_last_choice = choice
                        if is_correct:
                            st.session_state.quiz_score += 1
                        st.session_state.quiz_total += 1
                        st.session_state.quiz_history.append(
                            {
                                "question": q["question"],
                                "options": q["options"],
                                "selected": choice,
                                "correct": q["correct_option"],
                                "is_correct": is_correct,
                                "explanation": q["explanation"],
                            }
                        )
                        st.rerun()

        # B. Answer has been submitted: Evaluate and Explain
        else:
            choice = st.session_state.quiz_last_choice
            correct_opt = q["correct_option"]
            is_correct = (choice == correct_opt)

            st.markdown(f"### Question {st.session_state.quiz_total}")
            st.markdown(f"#### ❓ {q['question']}")

            # Feedback banner
            if is_correct:
                st.success(f"🎉 **Correct!** You chose **({choice})** {q['options'].get(choice, '')}")
            else:
                st.error(f"❌ **Not quite.** You chose **({choice})** {q['options'].get(choice, '')}")
                st.info(f"✅ **Correct Answer:** **({correct_opt})** {q['options'].get(correct_opt, '')}")

            # Deep educational explanation
            st.markdown("---")
            st.markdown(f"### 💡 Why?\n{q['explanation']}")
            st.markdown("---")

            # Progressive navigation
            next_col1, next_col2 = st.columns(2)
            with next_col1:
                if st.button("Next Question ➡️", type="primary", use_container_width=True):
                    st.session_state.quiz_current_q = None
                    st.session_state.quiz_answered = False
                    st.session_state.quiz_last_choice = None
                    st.rerun()

            with next_col2:
                summary_label = "View Performance Summary 📊"
                if st.session_state.quiz_total >= 5:
                    summary_label = f"Finish Quiz ({st.session_state.quiz_total} Done) & View Summary 🏆"

                if st.button(summary_label, use_container_width=True):
                    st.session_state.quiz_finished = True
                    st.rerun()

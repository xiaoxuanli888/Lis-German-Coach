import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Page configuration and styling ----------

st.set_page_config(
    page_title="Lis German Coach",
    page_icon="^_^",
    layout="centered",
)

CUSTOM_CSS = """
<style>
.main .block-container {
    max-width: 900px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

/* Card container */
.app-card {
    background: #ffffff;
    padding: 2rem 2.5rem;
    border-radius: 18px;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
    border: 1px solid rgba(148, 163, 184, 0.4);
}

/* Title + subtitle */
h1 {
    font-weight: 800 !important;
    letter-spacing: 0.04em;
}
.subtitle {
    color: #4b5563;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* Buttons */
.stButton > button {
    border-radius: 999px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
}

/* Text area */
textarea {
    border-radius: 14px !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- OpenAI client ----------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a friendly German teacher who helps learners build vocabulary
from A1 to C1 and prepare for Goethe B2/C1 exams. You respond in German
by default, but you may use very short English explanations when helpful.
Be encouraging and concise.
"""

def chat_with_ai(extra_instructions: str, user_message: str) -> str:
    """Small helper to talk to the OpenAI model."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": extra_instructions},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


# ---------- Sidebar ----------

with st.sidebar:
    st.title("Lis German Coach")
    st.caption("Vocabulary and Goethe exam practice, powered by OpenAI.")
    mode = st.radio(
        "Choose a mode:",
        ["Vocabulary practice (A1–C1)", "Exam practice (B2/C1)"],
        index=0,
    )

# ---------- Main card ----------

st.markdown(
    """
    <div class="app-card">
      <h1>Lis German Coach</h1>
      <p class="subtitle">
        Practice German vocabulary (A1–C1) and prepare for Goethe B2/C1 exams.
      </p>
    """,
    unsafe_allow_html=True,
)

# Make sure session state keys exist
for key in ["vocab_task", "vocab_feedback", "exam_task", "exam_feedback"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------- Vocabulary mode ----------

if mode.startswith("Vocabulary"):
    level = st.selectbox("Target level (CEFR):", ["A1", "A2", "B1", "B2", "C1"], index=3)
    st.write(f"You are practicing vocabulary at level **{level}**.")

    if st.button("New vocabulary exercise"):
        st.session_state["vocab_task"] = chat_with_ai(
            f"Create one short vocabulary exercise for CEFR level {level}.",
            (
                "Choose one useful German word or phrase for this level. "
                "Show the word and its English meaning in brackets. Then add a short task in German, "
                "for example asking the learner to translate it into English or use it in a sentence. "
                "Keep everything compact."
            ),
        )
        st.session_state["vocab_feedback"] = ""

    task = st.session_state["vocab_task"]
    if task:
        st.subheader("Exercise")
        st.write(task)

        answer = st.text_area("Your answer:", key="vocab_answer", height=120)

        if st.button("Check my answer"):
            st.session_state["vocab_feedback"] = chat_with_ai(
                f"The learner is practicing vocabulary at level {level}.",
                (
                    "Here is the exercise you gave them:\n"
                    f"{task}\n\n"
                    "Here is their answer:\n"
                    f"{answer}\n\n"
                    "Evaluate the answer as correct, partially correct, or incorrect. "
                    "Correct any mistakes, and provide one or two natural example sentences in German. "
                    "Use very short English explanations only when strictly necessary."
                ),
            )

    feedback = st.session_state["vocab_feedback"]
    if feedback:
        st.subheader("Feedback")
        st.write(feedback)

# ---------- Exam mode ----------

else:
    level = st.selectbox("Exam level:", ["B2", "C1"], index=0)
    st.write(f"You are practicing for Goethe level **{level}**.")

    if st.button("New exam-style task"):
        st.session_state["exam_task"] = chat_with_ai(
            f"Create one Goethe-style {level} exam task.",
            (
                f"Create one exam-style task for level {level}. It should resemble a Goethe writing or speaking task. "
                "Describe the task clearly in German but keep it fairly short."
            ),
        )
        st.session_state["exam_feedback"] = ""

    task = st.session_state["exam_task"]
    if task:
        st.subheader("Exam task")
        st.write(task)

        answer = st.text_area("Your response:", key="exam_answer", height=180)

        if st.button("Evaluate my response"):
            st.session_state["exam_feedback"] = chat_with_ai(
                f"You are evaluating a Goethe {level} exam-style answer.",
                (
                    f"Task:\n{task}\n\n"
                    f"Learner's answer:\n{answer}\n\n"
                    "Give feedback in German. Comment on content and structure, "
                    "correct the most important grammar and vocabulary mistakes, "
                    "suggest two or three improved sentences or phrases, and roughly estimate "
                    "whether the answer feels closer to B1, B2, or C1. "
                    "You may add very short English hints."
                ),
            )

    feedback = st.session_state["exam_feedback"]
    if feedback:
        st.subheader("Feedback")
        st.write(feedback)

# Close the card div
st.markdown("</div>", unsafe_allow_html=True)

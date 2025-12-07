import os
import re
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# ----------------- Setup -----------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"


SYSTEM_PROMPT = """
You are a friendly, supportive German teacher helping a learner prepare
for Goethe B2 and C1 exams and build vocabulary from A0 to C1.

Your style:
- Mostly answer in German, but use short English explanations if helpful.
- Be encouraging and not too formal.
- Keep answers fairly short (so they fit well in a terminal).
- Correct mistakes gently and clearly.
"""


def chat_with_ai(extra_instructions: str, user_message: str) -> str:
    """
    Helper function: send a message to the AI and get back text.
    """
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


# ----------------- Simple Progress Tracking (per session) -----------------

PROGRESS = {
    "vocab": {
        "total": 0,
        "correct": 0,
        "partial": 0,
        "incorrect": 0,
    },
    "exam": {
        "listening_attempts": 0,
        "reading_attempts": 0,
        "writing_attempts": 0,
        "speaking_attempts": 0,
    },
}


# ----------------- Helpers for Parsing Scores/Levels -----------------

def parse_vocab_score(feedback: str) -> Optional[str]:
    """
    Look for a line like:
    SCORE: correct
    SCORE: partially_correct
    SCORE: incorrect
    """
    match = re.search(r"SCORE:\s*(correct|partially_correct|incorrect)", feedback)
    return match.group(1) if match else None


def parse_exam_score(feedback: str) -> Optional[str]:
    """
    Look for a line like:
    SCORE: 3/4
    """
    match = re.search(r"SCORE:\s*(\d+/\d+)", feedback)
    return match.group(1) if match else None


def parse_exam_level(feedback: str) -> Optional[str]:
    """
    Look for a line like:
    LEVEL:B1
    LEVEL:B2
    LEVEL:C1
    """
    match = re.search(r"LEVEL:\s*(B1|B2|C1)", feedback)
    return match.group(1) if match else None


# ----------------- Vocabulary Mode -----------------

def normalize_level(level: str) -> str:
    """
    Treat A0 as "very basic", map to A1 for the AI.
    """
    level = level.upper()
    if level == "A0":
        return "A1"
    return level


def generate_de_to_en_task(level: str) -> str:
    """
    Ask AI to generate one German word + example sentence (no translation).
    """
    return chat_with_ai(
        f"You are creating one vocabulary exercise for CEFR level {level}.",
        (
            f"Choose ONE useful German word or short phrase appropriate for CEFR level {level}.\n"
            "Requirements:\n"
            "- The word/phrase must be in GERMAN.\n"
            "- DO NOT include the English translation.\n"
            "Output format exactly:\n"
            "WORD: <German word or phrase>\n"
            "SENTENCE: <One short example sentence in German using this word, level-appropriate.>\n\n"
            "No extra comments or explanation."
        ),
    )


def generate_en_to_de_task(level: str) -> str:
    """
    Ask AI to generate one English word (for the learner to translate into German).
    """
    return chat_with_ai(
        f"You are creating one vocabulary exercise for a German learner at CEFR level {level}.",
        (
            f"Choose ONE useful everyday ENGLISH word or short phrase for a learner around level {level}.\n"
            "The learner will translate it into GERMAN.\n"
            "Output format exactly:\n"
            "WORD: <English word or phrase>\n"
            "HINT: <Very short hint in English or German (optional, <= 10 words)>\n\n"
            "Do NOT include the German translation."
        ),
    )


def vocab_mode():
    print(f"\n{Color.CYAN}=== Vocabulary Trainer (A0–C1) ==={Color.RESET}")
    level = input("Which level? (A0, A1, A2, B1, B2, C1): ").strip().upper()
    if level not in ["A0", "A1", "A2", "B1", "B2", "C1"]:
        print(f"{Color.YELLOW}Unknown level – I'll choose B2.{Color.RESET}")
        level = "B2"
    mapped_level = normalize_level(level)

    print("\nChoose direction:")
    print("1) German → English  (see a German word, type the English meaning)")
    print("2) English → German  (see an English word, type the German translation)")

    direction = input("Your choice (1 or 2): ").strip()
    if direction not in ["1", "2"]:
        print(f"{Color.YELLOW}Unknown choice – I'll use 1 (German → English).{Color.RESET}")
        direction = "1"

    print(f"\nOkay, level {level}, direction: "
          f"{'German → English' if direction == '1' else 'English → German'}.")
    print("Type 'q' to return to the main menu.\n")

    while True:
        if direction == "1":
            # ----- German → English -----
            task = generate_de_to_en_task(mapped_level)
            print(f"\n{Color.BLUE}Task (German → English):{Color.RESET}")
            print(task)

            # Extract the word (optional: sentence)
            word_match = re.search(r"WORD:\s*(.+)", task)
            sentence_match = re.search(r"SENTENCE:\s*(.+)", task)
            german_word = word_match.group(1).strip() if word_match else ""
            german_sentence = sentence_match.group(1).strip() if sentence_match else ""

            user_answer = input(
                f"\nYour answer: What does '{german_word}' mean in English? (or 'q' to exit): "
            ).strip()
            if user_answer.lower() in ["q", "quit", "exit"]:
                print(f"{Color.DIM}Returning to main menu...{Color.RESET}\n")
                break

            feedback = chat_with_ai(
                "You are evaluating a German→English vocabulary translation.",
                (
                    f"German word: {german_word}\n"
                    f"Example sentence: {german_sentence}\n\n"
                    f"Learner's English translation: {user_answer}\n\n"
                    "Tasks:\n"
                    "1) Say if the English translation is correct, partly correct, or incorrect.\n"
                    "2) If needed, give 1–3 good English translations.\n"
                    "3) Give 1–2 example sentences in German (CEFR level appropriate).\n"
                    "4) Keep explanations short.\n\n"
                    "At the very end, on a new line, output exactly ONE of:\n"
                    "SCORE: correct\n"
                    "SCORE: partially_correct\n"
                    "SCORE: incorrect"
                ),
            )

        else:
            # ----- English → German -----
            task = generate_en_to_de_task(mapped_level)
            print(f"\n{Color.BLUE}Task (English → German):{Color.RESET}")
            print(task)

            word_match = re.search(r"WORD:\s*(.+)", task)
            hint_match = re.search(r"HINT:\s*(.+)", task)
            english_word = word_match.group(1).strip() if word_match else ""
            hint = hint_match.group(1).strip() if hint_match else ""

            if hint:
                print(f"\nHint: {hint}")

            user_answer = input(
                f"\nYour answer: How do you say '{english_word}' in German? (or 'q' to exit): "
            ).strip()
            if user_answer.lower() in ["q", "quit", "exit"]:
                print(f"{Color.DIM}Returning to main menu...{Color.RESET}\n")
                break

            feedback = chat_with_ai(
                "You are evaluating an English→German vocabulary translation.",
                (
                    f"English word/phrase: {english_word}\n"
                    f"Learner's German translation: {user_answer}\n\n"
                    "Tasks:\n"
                    "1) Say if the German translation is correct, partly correct, or incorrect.\n"
                    "2) Give 1–3 natural German translations.\n"
                    "3) If useful, mention article and plural form.\n"
                    "4) Give 1–2 example sentences in German.\n"
                    "5) Keep explanations short.\n\n"
                    "At the very end, on a new line, output exactly ONE of:\n"
                    "SCORE: correct\n"
                    "SCORE: partially_correct\n"
                    "SCORE: incorrect"
                ),
            )

        print(f"\n{Color.MAGENTA}Feedback:{Color.RESET}")
        print(feedback)
        print("\n" + "-" * 60)

        PROGRESS["vocab"]["total"] += 1
        score = parse_vocab_score(feedback)

        if score == "correct":
            PROGRESS["vocab"]["correct"] += 1
            print(f"{Color.GREEN}Recorded: correct ✔{Color.RESET}")
        elif score == "partially_correct":
            PROGRESS["vocab"]["partial"] += 1
            print(f"{Color.YELLOW}Recorded: partially correct ~{Color.RESET}")
        elif score == "incorrect":
            PROGRESS["vocab"]["incorrect"] += 1
            print(f"{Color.RED}Recorded: incorrect ✘{Color.RESET}")
        else:
            print(f"{Color.YELLOW}(Could not read score from feedback.){Color.RESET}")

        print("\n" + "-" * 60)


# ----------------- Exam Practice: Listening -----------------

def listening_mode(level: str):
    print(f"\n{Color.CYAN}=== Listening Practice ({level}) ==={Color.RESET}")
    print("Simulated listening: you read an 'audio script' and answer questions.")
    print("Type 'q' at any time to return.\n")

    while True:
        task = chat_with_ai(
            f"You are creating a Goethe-{level} style listening comprehension task.",
            (
                f"Create ONE listening comprehension task similar to Goethe {level}.\n"
                "Requirements:\n"
                "- Include an AUDIO script (what the learner 'hears'), 80–150 words.\n"
                "- Topic: everyday life, work, study, or society.\n"
                "- Then 3–5 comprehension questions in German, multiple choice (A–D).\n"
                "- Do NOT give the correct answers.\n\n"
                "Format exactly:\n"
                "AUDIO:\n"
                "<text>\n\n"
                "QUESTIONS:\n"
                "1) ....\n"
                "   A) ...\n"
                "   B) ...\n"
                "   C) ...\n"
                "   D) ...\n"
                "2) ....\n"
                "   A) ...\n"
                "   ...\n\n"
                "No extra explanation."
            ),
        )

        print(f"\n{Color.BLUE}Listening Task:{Color.RESET}")
        print(task)

        print("\nAnswer format suggestion: e.g. '1B 2D 3A' or 'B D A'.")
        user_answer = input("Your answers (or 'q' to exit): ").strip()
        if user_answer.lower() in ["q", "quit", "exit"]:
            print(f"{Color.DIM}Returning to exam menu...{Color.RESET}\n")
            break

        feedback = chat_with_ai(
            f"You are evaluating a Goethe-{level}-style listening task.",
            (
                "Here is the listening task:\n"
                f"{task}\n\n"
                "Learner's answers:\n"
                f"{user_answer}\n\n"
                "1) Decide which options are correct for each question.\n"
                "2) Compare with the learner's answers and say which are correct/incorrect.\n"
                "3) Give very short explanations in German.\n"
                "4) At the very end, on a new line, output the score as:\n"
                "SCORE: X/Y\n"
                "where X is the number of correct answers and Y is the total number of questions."
            ),
        )

        print(f"\n{Color.MAGENTA}Feedback:{Color.RESET}")
        print(feedback)

        PROGRESS["exam"]["listening_attempts"] += 1
        score_text = parse_exam_score(feedback)
        if score_text:
            print(f"{Color.GREEN}Recorded listening score: {score_text}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}(Could not read score from feedback.){Color.RESET}")

        print("\n" + "-" * 60)


# ----------------- Exam Practice: Reading -----------------

def reading_mode(level: str):
    print(f"\n{Color.CYAN}=== Reading Practice ({level}) ==={Color.RESET}")
    print("You read a text and answer questions.")
    print("Type 'q' at any time to return.\n")

    while True:
        task = chat_with_ai(
            f"You are creating a Goethe-{level} style reading comprehension task.",
            (
                f"Create ONE reading comprehension task similar to Goethe {level}.\n"
                "Requirements:\n"
                "- Provide a reading text of about 150–250 words.\n"
                "- Then 3–5 comprehension questions in German.\n"
                "- You may use multiple choice (A–D) or Richtig/Falsch.\n"
                "- Do NOT give the correct answers.\n\n"
                "Format:\n"
                "TEXT:\n"
                "<text>\n\n"
                "QUESTIONS:\n"
                "1) ...\n"
                "2) ...\n"
            ),
        )

        print(f"\n{Color.BLUE}Reading Task:{Color.RESET}")
        print(task)

        print("\nYou can answer in the format '1: ... 2: ...' or just write full sentences.")
        user_answer = input("Your answers (or 'q' to exit): ").strip()
        if user_answer.lower() in ["q", "quit", "exit"]:
            print(f"{Color.DIM}Returning to exam menu...{Color.RESET}\n")
            break

        feedback = chat_with_ai(
            f"You are evaluating a Goethe-{level}-style reading task.",
            (
                "Here is the reading task:\n"
                f"{task}\n\n"
                "Learner's answers:\n"
                f"{user_answer}\n\n"
                "1) Judge which answers are correct/partly correct/incorrect.\n"
                "2) Give short corrections or model answers in German.\n"
                "3) At the very end, on a new line, output an approximate score as:\n"
                "SCORE: X/Y\n"
                "where X is the number of mostly correct answers and Y is total questions."
            ),
        )

        print(f"\n{Color.MAGENTA}Feedback:{Color.RESET}")
        print(feedback)

        PROGRESS["exam"]["reading_attempts"] += 1
        score_text = parse_exam_score(feedback)
        if score_text:
            print(f"{Color.GREEN}Recorded reading score: {score_text}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}(Could not read score from feedback.){Color.RESET}")

        print("\n" + "-" * 60)


# ----------------- Exam Practice: Writing -----------------

def writing_mode(level: str):
    print(f"\n{Color.CYAN}=== Writing Practice ({level}) ==={Color.RESET}")
    print("You get a task (e.g. formal email, comment) and write a text.")
    print("Type 'q' at any time to return.\n")

    while True:
        task = chat_with_ai(
            f"Create one Goethe-style {level} writing task.",
            (
                f"Create ONE {level} writing task similar to the Goethe exam.\n"
                "Choose one typical format, for example:\n"
                "- short opinion/comment on a statement or graphic\n"
                "- formal email\n"
                "- short report or summary\n"
                "Give the task in German.\n"
                "Mention an approximate word count (e.g. 150–200 Wörter).\n"
                "Be clear but not too long."
            ),
        )

        print(f"\n{Color.BLUE}Writing Task:{Color.RESET}")
        print(task)

        print("\nWrite your text below. For multi-line input, you can write everything in one line.")
        user_answer = input("Your text (or 'q' to exit): ").strip()
        if user_answer.lower() in ["q", "quit", "exit"]:
            print(f"{Color.DIM}Returning to exam menu...{Color.RESET}\n")
            break

        feedback = chat_with_ai(
            f"You are evaluating a Goethe {level} writing task.",
            (
                f"Task:\n{task}\n\n"
                f"Learner's text:\n{user_answer}\n\n"
                "Give feedback in German (you may add very short English hints).\n"
                "1) Comment on content & structure.\n"
                "2) Correct important grammar and vocabulary mistakes.\n"
                "3) Suggest 2–4 improved sentences or phrases.\n"
                "4) Roughly say if this feels more like B1, B2, or C1.\n\n"
                "At the very end, on a new line, output exactly ONE of:\n"
                "LEVEL:B1\n"
                "LEVEL:B2\n"
                "LEVEL:C1"
            ),
        )

        print(f"\n{Color.MAGENTA}Feedback:{Color.RESET}")
        print(feedback)

        PROGRESS["exam"]["writing_attempts"] += 1
        level_est = parse_exam_level(feedback)
        if level_est:
            print(f"{Color.GREEN}Estimated writing level: {level_est}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}(Could not read estimated level.){Color.RESET}")

        print("\n" + "-" * 60)


# ----------------- Exam Practice: Speaking -----------------

def speaking_mode(level: str):
    print(f"\n{Color.CYAN}=== Speaking Practice ({level}) ==={Color.RESET}")
    print("You get a speaking task (Kurzvortrag, opinion, etc.) and type your answer.")
    print("Imagine you are speaking; write what you would say.")
    print("Type 'q' at any time to return.\n")

    while True:
        task = chat_with_ai(
            f"Create one Goethe-style {level} speaking task.",
            (
                f"Create ONE {level} speaking task similar to the Goethe exam.\n"
                "Examples:\n"
                "- short presentation on a topic with 3–4 guiding points\n"
                "- giving your opinion and arguments on a question\n"
                "- describing a graphic or situation\n"
                "Give the task in German.\n"
                "Be clear and not too long."
            ),
        )

        print(f"\n{Color.BLUE}Speaking Task:{Color.RESET}")
        print(task)

        print("\nType your answer as if you are speaking for about 2 minutes.")
        user_answer = input("Your answer (or 'q' to exit): ").strip()
        if user_answer.lower() in ["q", "quit", "exit"]:
            print(f"{Color.DIM}Returning to exam menu...{Color.RESET}\n")
            break

        feedback = chat_with_ai(
            f"You are evaluating a Goethe {level} speaking-style answer.",
            (
                f"Task:\n{task}\n\n"
                f"Learner's answer:\n{user_answer}\n\n"
                "Give feedback in German (you may add very short English hints).\n"
                "1) Comment on content (did they answer the task?) and structure.\n"
                "2) Comment on fluency and coherence (even though it is written).\n"
                "3) Correct important grammar and vocabulary mistakes.\n"
                "4) Suggest 2–3 improved sentences or phrases.\n"
                "5) Roughly say if this feels more like B1, B2, or C1.\n\n"
                "At the very end, on a new line, output exactly ONE of:\n"
                "LEVEL:B1\n"
                "LEVEL:B2\n"
                "LEVEL:C1"
            ),
        )

        print(f"\n{Color.MAGENTA}Feedback:{Color.RESET}")
        print(feedback)

        PROGRESS["exam"]["speaking_attempts"] += 1
        level_est = parse_exam_level(feedback)
        if level_est:
            print(f"{Color.GREEN}Estimated speaking level: {level_est}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}(Could not read estimated level.){Color.RESET}")

        print("\n" + "-" * 60)


# ----------------- Exam Mode (Menu) -----------------

def exam_mode():
    print(f"\n{Color.CYAN}=== Goethe Exam Trainer (B2 / C1) ==={Color.RESET}")
    level = input("Which exam level? (B2 or C1): ").strip().upper()
    if level not in ["B2", "C1"]:
        print(f"{Color.YELLOW}Unknown level – I'll choose B2.{Color.RESET}")
        level = "B2"

    while True:
        print(f"\n{Color.CYAN}Exam Menu ({level}):{Color.RESET}")
        print("1) Listening practice")
        print("2) Reading practice")
        print("3) Writing practice")
        print("4) Speaking practice")
        print("0) Back to main menu")

        choice = input("Please choose (0–4): ").strip()
        if choice == "1":
            listening_mode(level)
        elif choice == "2":
            reading_mode(level)
        elif choice == "3":
            writing_mode(level)
        elif choice == "4":
            speaking_mode(level)
        elif choice == "0":
            print(f"{Color.DIM}Back to main menu...{Color.RESET}\n")
            break
        else:
            print(f"{Color.RED}Invalid input, please try again.{Color.RESET}")


# ----------------- Show Progress -----------------

def show_progress():
    print(f"\n{Color.CYAN}=== Session Progress ==={Color.RESET}")

    v = PROGRESS["vocab"]
    print(f"\n{Color.BOLD}Vocabulary Trainer:{Color.RESET}")
    print(f"  Total exercises:   {v['total']}")
    print(f"  Correct:           {Color.GREEN}{v['correct']}{Color.RESET}")
    print(f"  Partially correct: {Color.YELLOW}{v['partial']}{Color.RESET}")
    print(f"  Incorrect:         {Color.RED}{v['incorrect']}{Color.RESET}")

    e = PROGRESS["exam"]
    print(f"\n{Color.BOLD}Exam Trainer:{Color.RESET}")
    print(f"  Listening tasks:   {e['listening_attempts']}")
    print(f"  Reading tasks:     {e['reading_attempts']}")
    print(f"  Writing tasks:     {e['writing_attempts']}")
    print(f"  Speaking tasks:    {e['speaking_attempts']}")

    print()


# ----------------- Main Menu -----------------

def main():
    print(f"{Color.BOLD}🇩🇪 Goethe AI Coach (A0–C1){Color.RESET}")
    print("This program uses the OpenAI API.")
    print("Make sure your API key is set in the environment variable OPENAI_API_KEY.\n")

    while True:
        print(f"{Color.CYAN}Main Menu:{Color.RESET}")
        print("1) Vocabulary Trainer (A0–C1)")
        print("2) Goethe Exam Trainer (B2/C1)")
        print("3) Show session progress")
        print("0) Exit")

        choice = input("Please choose (0–3): ").strip()

        if choice == "1":
            vocab_mode()
        elif choice == "2":
            exam_mode()
        elif choice == "3":
            show_progress()
        elif choice == "0":
            print(f"{Color.GREEN}Bye! Viel Erfolg beim Lernen! 👋{Color.RESET}")
            break
        else:
            print(f"{Color.RED}Invalid input, please try again.{Color.RESET}\n")


if __name__ == "__main__":
    main()

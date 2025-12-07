import os
from dotenv import load_dotenv
from openai import OpenAI

# -------------- Setup --------------

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a friendly, supportive German teacher helping a learner prepare
for Goethe B2 and C1 exams and build vocabulary from A1 to C1.

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


# -------------- Vocabulary Mode --------------

def vocab_mode():
    print("\n=== Wortschatz-Training (A1–C1) ===")
    level = input("Welches Niveau? (A1, A2, B1, B2, C1): ").strip().upper()
    if level not in ["A1", "A2", "B1", "B2", "C1"]:
        print("Unbekanntes Niveau – ich nehme B2.")
        level = "B2"

    print(f"\nOkay, wir üben Wortschatz auf Niveau {level}.")
    print("Ich gebe dir Aufgaben. Schreibe deine Antwort.")
    print("Gib 'q' ein, um zum Hauptmenü zurückzukehren.\n")

    while True:
        # 1) Ask AI to create one vocabulary exercise
        task = chat_with_ai(
            f"Create one short vocabulary exercise for CEFR level {level}.",
            (
                "Choose ONE useful German word or phrase for this level.\n"
                "Then:\n"
                "- Show the word,\n"
                "- briefly show its English meaning in brackets,\n"
                "- give a short task in German, e.g. 'Übersetze...', "
                "or 'Bilde einen Satz...'.\n"
                "Keep it compact."
            ),
        )

        print("\nAufgabe:")
        print(task)

        user_answer = input("\nDeine Antwort (oder 'q' zum Beenden): ").strip()
        if user_answer.lower() in ["q", "quit", "exit"]:
            print("Zurück zum Hauptmenü...\n")
            break

        # 2) Ask AI to give feedback on the user's answer
        feedback = chat_with_ai(
            f"The learner practices vocabulary at level {level}.",
            (
                "Here is the exercise you gave them:\n"
                f"{task}\n\n"
                "Here is their answer:\n"
                f"{user_answer}\n\n"
                "Evaluate the answer (correct / partly correct / incorrect).\n"
                "Correct mistakes. Give 1–2 natural example sentences in German.\n"
                "Use very short English explanations only if really needed."
            ),
        )

        print("\nFeedback:")
        print(feedback)
        print("\n" + "-" * 50)


# -------------- Exam Practice Mode --------------

def exam_mode():
    print("\n=== Goethe-Prüfungstraining (B2 / C1) ===")
    level = input("Für welches Niveau? (B2 oder C1): ").strip().upper()
    if level not in ["B2", "C1"]:
        print("Unbekanntes Niveau – ich nehme B2.")
        level = "B2"

    print(f"\nWir üben jetzt Aufgaben im Stil der Goethe-Prüfung {level}.")
    print("Ich gebe dir eine Schreib- oder Sprechaufgabe.")
    print("Du schreibst deine Antwort. Gib 'q' ein, um zurückzugehen.\n")

    while True:
        # 1) Ask AI for an exam-like task
        task = chat_with_ai(
            f"Create one Goethe-style {level} exam task.",
            (
                f"Create ONE {level} task similar to Goethe exam (writing or speaking).\n"
                "Examples:\n"
                "- Schreibe einen kurzen Kommentar zu einer Meinung.\n"
                "- Schreibe eine formelle E-Mail.\n"
                "- Halte einen kurzen Vortrag zu einem Thema.\n"
                "Explain the task in German. Be clear but not too long."
            ),
        )

        print("\nPrüfungsaufgabe:")
        print(task)

        answer = input("\nDeine Antwort (oder 'q' zum Beenden): ").strip()
        if answer.lower() in ["q", "quit", "exit"]:
            print("Zurück zum Hauptmenü...\n")
            break

        # 2) Ask AI to evaluate and give feedback
        feedback = chat_with_ai(
            f"You are evaluating a Goethe {level} exam-style answer.",
            (
                f"Task:\n{task}\n\n"
                f"Learner's answer:\n{answer}\n\n"
                "Give feedback in German (you may add very short English hints).\n"
                "1) Comment on content & structure.\n"
                "2) Correct important grammar and vocabulary mistakes.\n"
                "3) Suggest 2–3 improved sentences or phrases.\n"
                "4) Roughly say if this feels more like B1, B2, or C1."
            ),
        )

        print("\nFeedback:")
        print(feedback)
        print("\n" + "-" * 50)


# -------------- Main Menu --------------

def main():
    print("🇩🇪 Goethe Deutsch-Coach (B2/C1)")
    print("Dieses Programm benutzt die OpenAI-API.")
    print("Stelle sicher, dass deine API-Key und dein Konto funktionieren.\n")

    while True:
        print("Hauptmenü:")
        print("1) Wortschatz-Training (A1–C1)")
        print("2) Goethe-Prüfungstraining (B2/C1)")
        print("0) Beenden")

        choice = input("Bitte wähle (0–2): ").strip()

        if choice == "1":
            vocab_mode()
        elif choice == "2":
            exam_mode()
        elif choice == "0":
            print("Tschüss! Viel Erfolg beim Lernen! 👋")
            break
        else:
            print("Ungültige Eingabe, bitte noch einmal versuchen.\n")


if __name__ == "__main__":
    main()

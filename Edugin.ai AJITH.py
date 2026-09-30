import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

from gemini_client import is_configured
from qna import answer_question
from explanation_module import explain_topic
from quiz_module import generate_quiz
from summary_module import summarize_text
from learning_path import create_learning_path


app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def get_json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def required_text(data, key, default=""):
    value = data.get(key, default)
    return str(value).strip() if value is not None else default


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "EduGenie API",
            "gemini_configured": is_configured(),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        }
    )


@app.post("/api/qna")
def qna_api():
    data = get_json_body()

    question = required_text(data, "question")
    subject = required_text(data, "subject", "General")
    history = data.get("history", [])

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    try:
        answer = answer_question(question, subject, history)

        return jsonify(
            {
                "answer": answer
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/explain")
def explain_api():
    data = get_json_body()

    topic = required_text(data, "topic")
    level = required_text(data, "level", "College student")
    question = required_text(
        data,
        "question",
        "Explain the topic clearly with examples.",
    )

    if not topic:
        return jsonify({"error": "Please enter a topic."}), 400

    try:
        explanation = explain_topic(
            topic,
            level,
            question,
        )

        return jsonify(
            {
                "explanation": explanation
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/summary")
def summary_api():
    data = get_json_body()

    text = required_text(data, "text")
    length = required_text(data, "length", "medium")

    if not text:
        return jsonify(
            {
                "error": "Please paste notes or text to summarize."
            }
        ), 400

    try:
        summary = summarize_text(
            text,
            length,
        )

        return jsonify(
            {
                "summary": summary
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/quiz")
def quiz_api():
    data = get_json_body()

    topic = required_text(data, "topic")
    subject = required_text(data, "subject", "General")
    difficulty = required_text(data, "difficulty", "medium")

    try:
        count = int(data.get("count", 5))
    except (TypeError, ValueError):
        count = 5

    count = max(3, min(count, 15))

    if not topic:
        return jsonify(
            {
                "error": "Please enter a quiz topic."
            }
        ), 400

    try:
        questions = generate_quiz(
            topic,
            subject,
            difficulty,
            count,
        )

        return jsonify(
            {
                "questions": questions
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/learning-path")
def learning_path_api():
    data = get_json_body()

    subjects = data.get("subjects", [])

    if isinstance(subjects, str):
        subjects = [
            item.strip()
            for item in subjects.split(",")
            if item.strip()
        ]

    if not isinstance(subjects, list):
        subjects = []

    subjects = [
        str(item).strip()
        for item in subjects
        if str(item).strip()
    ][:8]

    goal = required_text(
        data,
        "goal",
        "Build a strong understanding of the subjects",
    )

    try:
        hours_per_day = float(
            data.get("hours_per_day", 2)
        )
    except (TypeError, ValueError):
        hours_per_day = 2

    hours_per_day = max(
        0.5,
        min(hours_per_day, 12),
    )

    try:
        days = int(data.get("days", 7))
    except (TypeError, ValueError):
        days = 7

    days = max(
        3,
        min(days, 30),
    )

    if not subjects:
        return jsonify(
            {
                "error": "Please enter at least one subject."
            }
        ), 400

    try:
        plan = create_learning_path(
            subjects,
            hours_per_day,
            days,
            goal,
        )

        return jsonify(
            {
                "plan": plan
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.errorhandler(413)
def too_large(_error):
    return jsonify(
        {
            "error": "The submitted content is too large. Please keep it under 2 MB."
        }
    ), 413


if __name__ == "__main__":
    port = int(
        os.getenv("PORT", "5000")
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "true",
        ).lower()
        == "true"
    )

    app.run(
        host="127.0.0.1",
        port=port,
        debug=debug,
    )
from __future__ import annotations

import os
from typing import TypedDict

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse


class Question(TypedDict):
    key: str
    prompt: str
    label: str


MORNING_QUESTIONS: list[Question] = [
    {"key": "full_name", "label": "Full name", "prompt": "Morning batch selected. What is your full name?"},
    {"key": "age", "label": "Age", "prompt": "What is your age?"},
    {"key": "course", "label": "Preferred course", "prompt": "Which course or subject do you want for the morning batch?"},
    {"key": "city", "label": "City", "prompt": "Which city are you from?"},
]

EVENING_QUESTIONS: list[Question] = [
    {"key": "full_name", "label": "Full name", "prompt": "Evening batch selected. What is your full name?"},
    {"key": "occupation", "label": "Occupation", "prompt": "What is your current occupation?"},
    {"key": "preferred_time", "label": "Preferred time", "prompt": "What evening time works best for you?"},
]

SESSIONS: dict[str, dict] = {}


def get_twilio_config_status() -> dict:
    return {
        "account_sid": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "auth_token": bool(os.getenv("TWILIO_AUTH_TOKEN")),
        "from_number": bool(os.getenv("TWILIO_PHONE_NUMBER")),
        "default_to_number": bool(os.getenv("TWILIO_DEFAULT_TO_NUMBER")),
    }


def handle_incoming_message(from_number: str, message_body: str) -> str:
    text = (message_body or "").strip()
    normalized = text.lower()

    if not from_number:
        return "Missing sender phone number."

    if normalized in {"restart", "start over", "reset"}:
        SESSIONS.pop(from_number, None)
        return _welcome_message()

    session = SESSIONS.get(from_number)
    if not session:
        session = {"stage": "choose_batch", "answers": {}, "batch": None}
        SESSIONS[from_number] = session

    if session["stage"] == "choose_batch":
        if normalized in {"hi", "hello", "hey", "start", ""}:
            return _welcome_message()

        batch = _parse_batch(normalized)
        if not batch:
            return _welcome_message()

        session["batch"] = batch
        session["stage"] = "collect_answers"
        session["question_index"] = 0
        return _current_question(session)

    if session["stage"] == "collect_answers":
        question = _get_questions(session["batch"])[session["question_index"]]
        session["answers"][question["key"]] = text
        session["question_index"] += 1

        questions = _get_questions(session["batch"])
        if session["question_index"] < len(questions):
            return _current_question(session)

        session["stage"] = "confirm"
        return _confirmation_message(session)

    if session["stage"] == "confirm":
        if normalized in {"yes", "y", "confirm"}:
            summary = _format_answers(session)
            SESSIONS.pop(from_number, None)
            return f"Confirmed. Here is your response:\n{summary}"

        if normalized in {"no", "n", "change"}:
            SESSIONS.pop(from_number, None)
            return "No problem. Let's start again.\n\n" + _welcome_message()

        return "Please reply YES to confirm or NO to restart."

    SESSIONS.pop(from_number, None)
    return _welcome_message()


def build_twiml_response(message: str) -> str:
    response = MessagingResponse()
    response.message(message)
    return str(response)


def send_start_message(to_number: str | None = None) -> dict:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    recipient = to_number or os.getenv("TWILIO_DEFAULT_TO_NUMBER")

    missing = [
        name
        for name, value in {
            "TWILIO_ACCOUNT_SID": account_sid,
            "TWILIO_AUTH_TOKEN": auth_token,
            "TWILIO_PHONE_NUMBER": from_number,
            "TWILIO_DEFAULT_TO_NUMBER": recipient,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing Twilio configuration: {', '.join(missing)}")

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=_welcome_message(),
        from_=from_number,
        to=recipient,
    )

    return {
        "sid": message.sid,
        "status": message.status,
        "to": recipient,
        "from": from_number,
    }


def _welcome_message() -> str:
    return (
        "Welcome to Tube Ranch batch registration.\n"
        "Please choose your batch: Morning or Evening.\n"
        "Reply RESTART anytime to begin again."
    )


def _parse_batch(value: str) -> str | None:
    if "morning" in value:
        return "morning"
    if "evening" in value:
        return "evening"
    return None


def _get_questions(batch: str) -> list[Question]:
    return MORNING_QUESTIONS if batch == "morning" else EVENING_QUESTIONS


def _current_question(session: dict) -> str:
    question = _get_questions(session["batch"])[session["question_index"]]
    return question["prompt"]


def _confirmation_message(session: dict) -> str:
    summary = _format_answers(session)
    return f"Please confirm your details:\n{summary}\nReply YES to confirm or NO to restart."


def _format_answers(session: dict) -> str:
    lines = [f"Batch: {session['batch'].title()}"]
    for question in _get_questions(session["batch"]):
        answer = session["answers"].get(question["key"], "-")
        lines.append(f"{question['label']}: {answer}")
    return "\n".join(lines)

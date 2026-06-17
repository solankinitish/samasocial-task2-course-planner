import os
from groq import Groq
from backend.schemas.models import SessionState, Message
from backend.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INTAKE_SYSTEM_PROMPT = """You are a course planning assistant helping a mentor design a course.
Collect information about:
1. Subject/topic area
2. Target audience (age group, skill level, prior knowledge)
3. Duration and session frequency
4. Learning goals and outcomes

Ask one question at a time. Be conversational and brief."""

async def stream_intake(session: SessionState, user_message: str):
    session.history.append(Message(role="user", content=user_message))
    messages = [{"role": m.role, "content": m.content} for m in session.history]

    logger.info("Intake turn in progress")

    full_response = ""
    stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
            *messages
        ],
        max_tokens=500,
        stream=True
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            full_response += token
            yield f"data: {token}\n\n"

    session.history.append(Message(role="assistant", content=full_response))
    yield "data: [DONE]\n\n"

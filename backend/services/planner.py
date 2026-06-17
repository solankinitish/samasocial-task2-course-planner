from backend.processors.session import create_session, get_session
from backend.processors.intake import stream_intake
from backend.processors.generator import generate_plan
from backend.processors.refiner import stream_refinement
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def new_session() -> str:
    return create_session()

async def chat(session_id: str, user_message: str):
    session = get_session(session_id)
    if session is None:
        yield "data: Session not found\n\n"
        return

    if session.course_plan is None:
        async for token in stream_intake(session, user_message):
            yield token
    else:
        async for token in stream_refinement(session, user_message):
            yield token

def generate(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise ValueError("Session not found")
    if not session.history:
        raise ValueError("No conversation history to generate plan from")
    plan = generate_plan(session.history)
    session.course_plan = plan
    return plan

def get_plan(session_id: str):
    session = get_session(session_id)
    if session is None:
        return None
    return session.course_plan

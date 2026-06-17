import os
import json
from groq import Groq
from backend.schemas.models import CoursePlan, Message
from backend.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REFINE_SYSTEM_PROMPT = """You are a course planning assistant. The mentor wants to refine their course plan.
Based on their refinement request and the current plan, return an updated plan.
Return ONLY valid JSON matching the exact same schema as the current plan, no other text, no markdown.
Every module MUST have these fields: title, learning_objectives, lessons, prerequisites, assessment.
Every lesson MUST have these fields: title, objective, resources, difficulty.
Every resource MUST have these fields: title, url, type.
Do not drop any fields from the schema."""

def refine_plan(current_plan: CoursePlan, refinement: str) -> CoursePlan:
    logger.info(f"Refining plan: {refinement}")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": REFINE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Current plan:\n{current_plan.model_dump_json()}\n\nRefinement request: {refinement}"}
        ],
        max_tokens=4000
    )
    raw = response.choices[0].message.content.strip()
    parsed = json.loads(raw)
    return CoursePlan(**parsed)

async def stream_refinement(session, user_message: str):
    logger.info(f"Refinement request: {user_message}")
    try:
        plan = refine_plan(session.course_plan, user_message)
        session.course_plan = plan
        response_text = "I've updated the course plan based on your request."
        session.history.append(Message(role="assistant", content=response_text))
        yield f"data: {response_text}\n\n"
        yield f"data: PLAN_READY:{plan.model_dump_json()}\n\n"
    except Exception as e:
        logger.error(f"Refinement failed: {str(e)}")
        yield f"data: [Error refining plan: {str(e)}]\n\n"
    yield "data: [DONE]\n\n"

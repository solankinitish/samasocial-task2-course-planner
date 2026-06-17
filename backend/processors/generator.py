import os
import json
from groq import Groq
from backend.schemas.models import CoursePlan, Message
from backend.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
PLAN_SYSTEM_PROMPT = """You are a course plan generator. Output ONLY a valid JSON object. No text before or after. No markdown. No explanation. No questions.

The JSON must follow this exact structure:
{
    "course_title": "string",
    "target_audience": "string",
    "duration": "string",
    "learning_goals": ["string"],
    "modules": [
        {
            "title": "string",
            "learning_objectives": ["string"],
            "prerequisites": ["string"],
            "assessment": "string",
            "lessons": [
                {
                    "title": "string",
                    "objective": "string",
                    "difficulty": "beginner",
                    "resources": [
                        {
                            "title": "string",
                            "url": "string",
                            "type": "video"
                        }
                    ]
                }
            ]
        }
    ]
}

Output the JSON and nothing else."""

def generate_plan(history: list[Message]) -> CoursePlan:
    logger.info("Generating course plan from intake history")
    messages = [{"role": m.role, "content": m.content} for m in history]
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            *messages,
            {"role": "user", "content": "Generate the course plan as JSON now."}
        ],
        max_tokens=4000
    )
    raw = response.choices[0].message.content.strip()
    logger.info(f"Raw plan response length: {len(raw)}")
    logger.info(f"Raw plan response: {raw[:200]}")

    # Extract JSON if wrapped in markdown
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    # Find JSON object if mixed with text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    parsed = json.loads(raw, strict=False)
    return CoursePlan(**parsed)

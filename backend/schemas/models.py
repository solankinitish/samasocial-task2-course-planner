from pydantic import BaseModel
from typing import Literal, Any

class Resource(BaseModel):
    title: str
    url: str
    type: str

class Lesson(BaseModel):
    title: str
    objective: str
    resources: list[Resource]
    difficulty: Literal["beginner", "intermediate", "advanced"]

class Module(BaseModel):
    title: str
    learning_objectives: list[str]
    lessons: list[Lesson]
    prerequisites: list[str]
    assessment: str

class CoursePlan(BaseModel):
    course_title: str
    target_audience: str
    duration: str
    learning_goals: list[str]
    modules: list[Module]

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class SessionState(BaseModel):
    history: list[Message] = []
    course_plan: CoursePlan | None = None

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.services import planner as planner_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class SessionResponse(BaseModel):
    session_id: str

@router.post("/session/create", response_model=SessionResponse)
async def create_session():
    session_id = planner_service.new_session()
    return SessionResponse(session_id=session_id)

@router.post("/session/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest):
    return StreamingResponse(
        planner_service.chat(session_id, request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@router.post("/session/{session_id}/generate")
async def generate(session_id: str):
    try:
        plan = planner_service.generate(session_id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@router.get("/session/{session_id}/plan")
async def get_plan(session_id: str):
    plan = planner_service.get_plan(session_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="No plan generated yet")
    return plan

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.server import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Course Planner",
    description="Conversational assistant that helps mentors design structured course plans",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}

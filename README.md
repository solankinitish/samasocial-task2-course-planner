# AI Course Planning Assistant
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Groq](https://img.shields.io/badge/LLM-Groq-orange)
![Cloud Run](https://img.shields.io/badge/Deployed-Cloud_Run-blue)

A conversational AI assistant that helps mentors design structured courses through guided back-and-forth conversation. The mentor describes their course, the assistant asks follow-up questions, and generates a fully structured course plan that can be refined, edited, and exported as JSON.

**Live:** https://task2-frontend-915504862406.us-central1.run.app  
**Backend API:** https://task2-backend-915504862406.us-central1.run.app/docs

---

## What it does

Have a conversation about your course. When ready, click Generate — the assistant produces a structured plan with modules, lessons, resources, difficulty levels, and assessments. Refine any part by continuing the conversation. Export the final plan as JSON.

---

## Architecture

```
Streamlit Frontend (split panel: chat left, plan right)
       ↓ HTTP + SSE
FastAPI Backend
       ↓
services/planner.py (thin orchestrator)
       ↓
processors/
├── session.py    — session creation and retrieval
├── intake.py     — conversational intake, streaming
├── generator.py  — structured JSON plan generation
└── refiner.py    — plan refinement from mentor requests
```

---

## Key Decisions

**processors/ module — one responsibility per file**  
Intake, generation, refinement, and session management each live in their own file under `processors/`. `services/planner.py` is a thin orchestrator that routes to the right processor based on session state. This keeps each file small, ownable, and independently testable.

**Explicit Generate button over LLM signal detection**  
An earlier approach appended `INTAKE_COMPLETE` to the prompt and tried to detect it mid-stream. The LLM returned it with spaces ("INT AKE COMPLETE"), inconsistently, or not at all. Removed entirely. The mentor clicks Generate when ready — explicit user intent is more reliable than LLM self-reporting.

**Session state drives routing, no mode flag**  
`course_plan is None` → route to intake. `course_plan is not None` → route to refinement. No `intake_complete` boolean, no explicit mode switching. State is the router.

**Separate /generate endpoint**  
Plan generation is a distinct action from conversation — it's expensive, structured, and mentor-initiated. Keeping it as a separate `POST /session/{id}/generate` endpoint makes the API contract clear and gives the frontend a clean trigger point.

**JSON extraction pipeline**  
The LLM doesn't always return clean JSON — it sometimes wraps in markdown fences, prepends conversational text, or includes control characters. Three-step extraction: strip markdown fences → find `{` to `}` boundaries → `json.loads(raw, strict=False)`. Handles all observed LLM output variance without regex.

**Nested CoursePlan schema covers bonus requirements at zero cost**  
`CoursePlan → modules[] → lessons[] → resources[]`. `difficulty` (beginner/intermediate/advanced) is a field on every lesson. `prerequisites` is a list on every module. `assessment` is a string on every module. Bonus requirements covered by schema design — no extra prompt engineering or logic needed.

**Full plan replacement on refinement**  
The refiner receives the full current plan as JSON plus the mentor's refinement request, and returns a complete updated plan. Not a diff or patch — full replacement. Simpler, and the LLM has complete context to make coherent changes across modules.

---

## Local Setup

**Requirements:** Python 3.11+, Groq API key (free at console.groq.com)

```bash
git clone https://github.com/solankinitish/samasocial-task2-course-planner
cd samasocial-task2-course-planner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
GROQ_API_KEY=your-key-here
```

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
streamlit run frontend/app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Required. Get free at console.groq.com |
| `BACKEND_URL` | Frontend → backend URL. Defaults to `http://127.0.0.1:8000/api/v1` |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/session/create` | Create session |
| POST | `/api/v1/session/{id}/chat` | Streaming chat — intake or refinement |
| POST | `/api/v1/session/{id}/generate` | Generate structured course plan |
| GET | `/api/v1/session/{id}/plan` | Fetch current plan as JSON |

---

## Tradeoffs

- Session state is in-memory — server restart clears sessions. Production would use Redis or a database.
- Plan generation makes a non-streaming LLM call — the UI shows a spinner during this (~3-5 seconds). Streaming structured JSON would require a different parsing approach.
- Resources in the generated plan are suggested by the LLM and not verified for availability — production would validate URLs.

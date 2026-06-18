import streamlit as st
import requests
import json
import os

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/v1")

def create_session():
    response = requests.post(f"{BASE_URL}/session/create")
    return response.json()["session_id"]

def stream_chat(session_id, message):
    try:
        with requests.post(
            f"{BASE_URL}/session/{session_id}/chat",
            json={"message": message},
            stream=True,
            timeout=60
        ) as response:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        token = decoded[6:]
                        if token != "[DONE]":
                            if token.startswith("PLAN_READY:"):
                                plan_json = token[len("PLAN_READY:"):]
                                st.session_state.plan = json.loads(plan_json)
                                st.session_state.edited_plan = json.loads(plan_json)
                            else:
                                yield token
    except requests.exceptions.ChunkedEncodingError:
        return
    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"

def generate_plan(session_id):
    response = requests.post(f"{BASE_URL}/session/{session_id}/generate")
    if response.status_code == 200:
        return response.json()
    else:
        return None

def export_plan(plan):
    return json.dumps(plan, indent=2)

# --- Init session state ---
if "session_id" not in st.session_state:
    st.session_state.session_id = create_session()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "edited_plan" not in st.session_state:
    st.session_state.edited_plan = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# --- Page config ---
st.set_page_config(page_title="AI Course Planner", layout="wide")
st.title("🎓 AI Course Planner")

# --- Split layout ---
chat_col, plan_col = st.columns([1, 1])

# --- Chat Panel ---
with chat_col:
    st.subheader("💬 Course Planning Chat")

    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    user_input = st.text_input("Tell me about your course...", key=f"user_input_{st.session_state.input_key}", label_visibility="collapsed")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        send = st.button("Send", use_container_width=True)
    with col2:
        generate = st.button("🚀 Generate", use_container_width=True, type="primary")

    if send and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                response_text = st.write_stream(stream_chat(st.session_state.session_id, user_input))
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.session_state.input_key += 1
        st.rerun()

    if generate:
        with st.spinner("Generating your course plan..."):
            plan = generate_plan(st.session_state.session_id)
        if plan:
            st.session_state.plan = plan
            st.session_state.edited_plan = plan.copy()
            st.rerun()
        else:
            st.error("Failed to generate plan. Have a conversation first.")

# --- Plan Panel ---
with plan_col:
    st.subheader("📋 Course Plan")

    if st.session_state.edited_plan is None:
        st.info("Start a conversation and click 'Generate' to see your plan here.")
    else:
        plan = st.session_state.edited_plan

        with st.container(height=700):
            plan["course_title"] = st.text_input("Course Title", value=plan.get("course_title", ""))
            plan["target_audience"] = st.text_input("Target Audience", value=plan.get("target_audience", ""))
            plan["duration"] = st.text_input("Duration", value=plan.get("duration", ""))

            st.markdown("**Learning Goals**")
            goals = plan.get("learning_goals", [])
            updated_goals = []
            for i, goal in enumerate(goals):
                updated_goals.append(st.text_input(f"Goal {i+1}", value=goal, key=f"goal_{i}"))
            plan["learning_goals"] = updated_goals

            st.divider()

            for m_idx, module in enumerate(plan.get("modules", [])):
                with st.expander(f"📦 {module.get('title', f'Module {m_idx+1}')}", expanded=m_idx == 0):
                    module["title"] = st.text_input("Module Title", value=module.get("title", ""), key=f"mod_title_{m_idx}")
                    module["assessment"] = st.text_input("Assessment", value=module.get("assessment", ""), key=f"mod_assess_{m_idx}")

                    prereqs = module.get("prerequisites", [])
                    if prereqs:
                        st.markdown(f"**Prerequisites:** {', '.join(prereqs)}")

                    for l_idx, lesson in enumerate(module.get("lessons", [])):
                        st.markdown(f"**Lesson {l_idx+1}:**")
                        lesson["title"] = st.text_input("Title", value=lesson.get("title", ""), key=f"les_title_{m_idx}_{l_idx}")
                        lesson["objective"] = st.text_input("Objective", value=lesson.get("objective", ""), key=f"les_obj_{m_idx}_{l_idx}")
                        st.caption(f"Difficulty: {lesson.get('difficulty', 'N/A')}")

                        for r_idx, resource in enumerate(lesson.get("resources", [])):
                            st.markdown(f"- [{resource.get('title')}]({resource.get('url')}) `{resource.get('type')}`")

        st.download_button(
            label="⬇️ Export as JSON",
            data=export_plan(st.session_state.edited_plan),
            file_name="course_plan.json",
            mime="application/json",
            use_container_width=True
        )

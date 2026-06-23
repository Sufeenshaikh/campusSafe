# AI Safety Assistant chat page.
#
# How it works:
#   1. Student types a question
#   2. Agent decides which tool to use (check_zone or past_incidents)
#   3. Tool runs and gets a result from database or ChromaDB
#   4. RAG searches for relevant past incidents
#   5. Ollama generates the final answer using all context
#   6. Response is shown and saved to chat history
#
# Chat history lives in st.session_state
# so the AI remembers the conversation while the tab is open.

import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "AI Assistant — CampusSafe",
    page_icon  = "🤖",
    layout     = "centered"
)

# ── LOGIN GUARD ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("Please login first.")
    st.stop()

user = st.session_state.user

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_message" not in st.session_state:
    st.session_state.pending_message = None


# ── CHECK OLLAMA IS RUNNING ───────────────────────────────────────────────────
# Before anything else, check if Ollama is reachable.
# This gives a clear error message instead of silently failing.
def ollama_is_running():
    """
    Sends a simple ping to Ollama.
    Returns True if Ollama is running, False if not.
    """
    import requests
    try:
        response = requests.get(
            "http://localhost:11434",
            timeout = 3
        )
        return response.status_code == 200
    except Exception:
        return False


# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🤖 AI Safety Assistant")
st.caption("Ask anything about campus safety. Powered by Ollama locally.")
st.write("---")

# ── OLLAMA STATUS CHECK ───────────────────────────────────────────────────────
# Show this check at the top so the user knows immediately
# if Ollama is not running before they try to chat.
if not ollama_is_running():
    st.error(
        "Ollama is not running. "
        "Open a new terminal and run this command, then refresh this page:"
    )
    st.code("ollama serve", language="bash")
    st.stop()
    # st.stop() means nothing below this runs
    # The page shows only the error until Ollama is started

# If we get here Ollama is running — show green status
st.success("Ollama is running — AI ready.")
st.write(" ")

#HELPER- PROCESS ONE MESSAGE
def process_message(user_input):
    from ai import run_agent_stream

    with st.chat_message("user"):
        st.write(user_input)

    # Stream AI response
    with st.chat_message("assistant"):
        # with st.spinner("Thinking..."):
            try:
                response = st.write_stream(
                    run_agent_stream(
                    user_question=user_input,
                    chat_history=st.session_state.chat_history
                  )
                 )
                
            except Exception as e:
                response = f"Error: {str(e)}. "
                st.write(response)
    
    # Only append to history if a response was successfully generated/captured
    if response:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )
        st.session_state.chat_history.append(
            {"role": "assistant", "content": response}
        )

    


# ── HOW IT WORKS ──────────────────────────────────────────────────────────────
with st.expander("How does this AI work?"):
    st.write(
        "**Agent:** Before answering, the AI decides which tool to use:\n"
        "- *Check zone tool* — reads live safety levels from the database\n"
        "- *Past incidents tool* — searches ChromaDB for similar events\n\n"
        "**RAG:** Every incident report is stored as a vector in ChromaDB. "
        "The AI finds the 3 most relevant past incidents before answering.\n\n"
        "**Ollama:** Runs on this machine only. No internet used."
    )


# ── SUGGESTED QUESTIONS ───────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.subheader("Try asking:")
    st.write(" ")

    suggestions = [
        "Is it safe to walk to the library at 10pm?",
        "Which areas should I avoid at night?",
        "What incidents happened near the hostel?",
        "Is the parking area safe right now?",
    ]

    col1, col2 = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        col = col1 if i % 2 == 0 else col2
        if col.button(
            suggestion,
            key              = f"suggestion_{i}",
            use_container_width = True
        ):
            st.session_state.chat_history.append({
                "role":    "user",
                "content": suggestion
            })
            st.rerun()

    st.write("---")

#PROCESS PENDING SUGGESSTIONS
if st.session_state.pending_message:
    pending = st.session_state.pending_message
    st.session_state.pending_message = None
    process_message(pending)
    st.rerun()


# ── DISPLAY CHAT HISTORY ──────────────────────────────────────────────────────
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# ── CHAT INPUT ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask a safety question...")

if user_input:
    process_message(user_input)


# ── CLEAR CHAT ────────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.write(" ")
    if st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()


# ── WHAT THE AI KNOWS ─────────────────────────────────────────────────────────
st.write("---")
st.subheader("What the AI knows right now")

from database import get_all_zones, get_recent_reports
zones   = get_all_zones()
reports = get_recent_reports(days=7)

col1, col2, col3 = st.columns(3)
col1.metric("Campus zones",      len(zones))
col2.metric("Reports in memory", len(reports))
col3.metric(
    "Unsafe zones",
    sum(1 for z in zones if z["safety_level"] == "unsafe")
)

with st.expander("Current zone safety levels"):
    for zone in zones:
        emoji = (
            "🟢" if zone["safety_level"] == "safe"
            else "🟡" if zone["safety_level"] == "caution"
            else "🔴"
        )
        st.write(f"{emoji} **{zone['name']}** — {zone['description']}")
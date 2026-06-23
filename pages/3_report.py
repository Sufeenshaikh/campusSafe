import streamlit as st
from datetime import datetime
from database import (
    save_report,
    get_all_reports,
    get_all_zones
)
from ai import (
    get_final_severity,
    store_incident_in_rag,
    auto_update_zones
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "Report Incident — CampusSafe",
    page_icon   = "📝",
    layout      = "centered"
)

# ── LOGIN GUARD ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("Please login first.")
    st.stop()

user = st.session_state.user


# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("📝 Report an Incident")
st.caption(
    "Submit a safety concern. "
    "AI will automatically analyse your report and update the campus map."
)
st.write("---")


# ── REPORT FORM ───────────────────────────────────────────────────────────────
st.subheader("Incident Details")
st.write(" ")

# Get zone names from database for the dropdown
zones      = get_all_zones()
zone_names = [z["name"] for z in zones]

# Add an "Other" option in case the zone is not listed
zone_names_with_other = zone_names + ["Other (type below)"]

selected = st.selectbox(
    "Where did this happen?",
    zone_names_with_other,
    key="report_zone"
)

# If they pick Other, show a text input for custom location
if selected == "Other (type below)":
    location_name = st.text_input(
        "Describe the location",
        placeholder = "Example: Near the water tank behind Block C",
        key         = "custom_location"
    )
else:
    location_name = selected

st.write(" ")

description = st.text_area(
    "What happened?",
    placeholder = (
        "Describe what you saw or experienced. "
        "Be as specific as possible — time, people, situation."
    ),
    height  = 140,
    key     = "report_description"
)

st.write(" ")

# Severity slider — user gives their own rating
# AI will compare this with its sentiment score
# and use whichever is higher
user_severity = st.slider(
    "How serious was this? (your rating)",
    min_value = 1,
    max_value = 5,
    value     = 3,
    key       = "report_severity",
    help      = "1 = Minor concern   5 = Critical emergency"
)

# Show what each severity level means
severity_labels = {
    1: "🟢 Minor — something felt slightly off",
    2: "🟡 Low — worth noting but not urgent",
    3: "🟠 Medium — caused concern or discomfort",
    4: "🔴 High — felt unsafe or threatened",
    5: "🆘 Critical — immediate danger or serious incident"
}
st.caption(severity_labels[user_severity])

st.write(" ")

# ── SUBMIT BUTTON ─────────────────────────────────────────────────────────────
submit = st.button(
    "Submit Report",
    use_container_width = True,
    type                = "primary"
)

if submit:

    # ── Validation ────────────────────────────────────────────────────────────
    if not location_name:
        st.error("Please select or enter a location.")
        st.stop()

    if not description or len(description.strip()) < 10:
        st.error("Please describe what happened (at least 10 characters).")
        st.stop()

    # ── AI Step 1: Sentiment Analysis ─────────────────────────────────────────
    with st.spinner("Analysing your report..."):

        # Compare user severity with AI sentiment score
        # Use whichever is higher
        final_severity = get_final_severity(
            description        = description,
            user_given_severity = user_severity
        )

    # ── AI Step 2: Save to Database ───────────────────────────────────────────
    save_report(
        user_id       = user["id"],
        user_name     = user["name"],
        location_name = location_name,
        description   = description,
        severity      = final_severity
    )

    # We need the report ID for ChromaDB
    # Get it by reading the most recent report for this user
    from database import get_user_reports
    latest = get_user_reports(user["id"])
    report_id = latest[0]["id"] if latest else None

    # ── AI Step 3: Store in ChromaDB for RAG ──────────────────────────────────
    if report_id:
        store_incident_in_rag(
            report_id   = report_id,
            location    = location_name,
            description = description,
            severity    = final_severity
        )

    # ── AI Step 4: Update Zone Safety Levels ──────────────────────────────────
    with st.spinner("Updating campus safety map..."):
        changes = auto_update_zones()

    # ── Show Result ───────────────────────────────────────────────────────────
    st.write(" ")
    st.success("Report submitted successfully. Thank you for keeping campus safe.")
    st.write(" ")

    # Show what the AI did
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Your severity rating",  user_severity)

    with col2:
        # Show if AI adjusted it
        if final_severity > user_severity:
            st.metric(
                "AI adjusted severity",
                final_severity,
                delta = f"+{final_severity - user_severity} (text sounds serious)"
            )
        else:
            st.metric("AI severity score", final_severity)

    st.write(" ")

    # Show which zones the AI updated
    if changes:
        st.warning("Map updated by AI based on your report:")
        for change in changes:
            st.write(f"  • {change}")
    else:
        st.info(
            "No zone safety levels changed. "
            "Your report has been recorded and added to AI memory."
        )

    # Sentiment explanation
    st.write(" ")
    with st.expander("How did AI analyse your report?"):
        from ai import analyze_sentiment
        from textblob import TextBlob

        polarity = TextBlob(description).sentiment.polarity
        ai_score = analyze_sentiment(description)

        st.write(
            f"**TextBlob polarity score:** {polarity:.2f}  "
            f"(range: -1.0 = very negative to +1.0 = very positive)"
        )
        st.write(f"**AI severity from text:** {ai_score} out of 5")
        st.write(f"**Your severity rating:** {user_severity} out of 5")
        st.write(f"**Final severity used:** {final_severity} out of 5")
        st.caption(
            "The AI reads the emotion in your words and scores it. "
            "If the text sounds more serious than your rating, "
            "the AI score is used instead."
        )


# ── ALL REPORTS ───────────────────────────────────────────────────────────────
st.write("---")
st.subheader("Recent Campus Reports")
st.caption("Reports submitted by all students.")

reports = get_all_reports()

if not reports:
    st.info(
        "No reports yet. "
        "Be the first to report a safety concern."
    )

else:
    # Severity color mapping
    severity_colors = {
        1: "🟢", 2: "🟡",
        3: "🟠", 4: "🔴", 5: "🆘"
    }

    for report in reports[:20]:   # show latest 20

        severity_icon = severity_colors.get(
            report["severity"], "⚪"
        )

        with st.expander(
            f"{severity_icon} {report['location_name']}  —  "
            f"{report['reported_at'][:16]}"
        ):
            st.write(f"**Description:** {report['description']}")

            col1, col2, col3 = st.columns(3)
            col1.write(f"**Severity:** {report['severity']}/5")
            col2.write(f"**Reported by:** {report['user_name']}")
            col3.write(f"**Time:** {report['reported_at'][11:16]}")

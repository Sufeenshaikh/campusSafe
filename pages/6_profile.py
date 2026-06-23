# Student profile page.
#
# Shows the logged in student's account details.
# Lets them update their guardian email.
# Shows their personal SOS history and incident reports.

import streamlit as st
from database import (
    resolve_sos,
    update_guardian_email,
    get_user_sos,
    get_user_reports
)
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "My Profile — CampusSafe",
    page_icon  = "👤",
    layout     = "centered"
)

# ── LOGIN GUARD ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("Please login first.")
    st.stop()

user = st.session_state.user


# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("👤 My Profile")
st.caption(f"Logged in as {user['role'].capitalize()}")
st.write("---")


# ── ACCOUNT DETAILS ───────────────────────────────────────────────────────────
st.subheader("Account Details")
st.write(" ")

col1, col2 = st.columns(2)
col1.write(f"**Name**")
col1.write(f"**Email**")
col1.write(f"**Role**")
col1.write(f"**Member since**")

# Format created_at nicely
created = user.get("created_at", "")
if created:
    try:
        dt = datetime.strptime(created[:19], "%Y-%m-%d %H:%M:%S")
        created = dt.strftime("%d %B %Y")
    except Exception:
        created = created[:10]

col2.write(user["name"])
col2.write(user["email"])
col2.write(user["role"].capitalize())
col2.write(created)

st.write("---")


# ── GUARDIAN EMAIL ────────────────────────────────────────────────────────────
st.subheader("Guardian Contact")
st.caption(
    "Your guardian receives an email whenever you press SOS. "
    "Make sure this is correct."
)
st.write(" ")

current_guardian = user.get("guardian_email", "")

if current_guardian:
    st.info(f"📧 Current guardian email: **{current_guardian}**")
else:
    st.warning("No guardian email set. Please add one below.")

st.write(" ")

new_guardian = st.text_input(
    "Update guardian email",
    placeholder = "guardian@email.com",
    key         = "new_guardian_email"
)

if st.button("Save Guardian Email", use_container_width=True):
    if not new_guardian:
        st.error("Please enter an email address.")
    elif "@" not in new_guardian:
        st.error("Please enter a valid email address.")
    else:
        update_guardian_email(user["id"], new_guardian)

        # Update session state so the change reflects immediately
        st.session_state.user["guardian_email"] = new_guardian

        st.success(f"Guardian email updated to {new_guardian}")

st.write("---")


# ── MY STATS ─────────────────────────────────────────────────────────────────
st.subheader("My Activity")
st.write(" ")

my_sos     = get_user_sos(user["id"])
my_reports = get_user_reports(user["id"])

col1, col2, col3 = st.columns(3)

col1.metric(
    "SOS Alerts Sent",
    len(my_sos)
)
col2.metric(
    "Reports Submitted",
    len(my_reports)
)
col3.metric(
    "Active Alerts",
    sum(1 for s in my_sos if s["status"] == "active")
)

st.write("---")


# ── MY SOS HISTORY ────────────────────────────────────────────────────────────
st.subheader("My SOS History")

if not my_sos:
    st.caption("No SOS alerts sent yet. Stay safe!")
else:
    for i, alert in enumerate(my_sos, start=1):
        status_icon = "🔴" if alert["status"] == "active" else "🟢"
        maps_link   = (
            f"https://maps.google.com/?"
            f"q={alert['latitude']},{alert['longitude']}"
        )

        with st.expander(
            f"{status_icon} Your Alert #{i} — "
            f"{alert['triggered_at'][:16]}"
        ):
            col1, col2 = st.columns(2)
            col1.write(f"**Status:** {alert['status'].capitalize()}")
            col2.write(f"**Time:** {alert['triggered_at'][11:16]}")
            st.markdown(f"[📍 View location on Google Maps]({maps_link})")

            if alert["status"] == "active":
                if st.button(
                    "Mark as Resolved",
                    key = f"profile_resolve_{alert['id']}"
                ):
                    from database import resolve_sos
                    resolve_sos(alert["id"])
                    st.success("Marked as resolved.")
                    st.rerun()

st.write("---")


# ── MY REPORTS ────────────────────────────────────────────────────────────────
st.subheader("My Incident Reports")

if not my_reports:
    st.caption("No reports submitted yet.")
else:
    severity_icon = {
        1: "🟢", 2: "🟡",
        3: "🟠", 4: "🔴", 5: "🆘"
    }

    for report in my_reports:
        icon = severity_icon.get(report["severity"], "⚪")

        with st.expander(
            f"{icon} {report['location_name']} — "
            f"{report['reported_at'][:16]}"
        ):
            st.write(f"**{report['description']}**")
            col1, col2 = st.columns(2)
            col1.caption(f"Severity: {report['severity']}/5")
            col2.caption(f"Time: {report['reported_at'][11:16]}")
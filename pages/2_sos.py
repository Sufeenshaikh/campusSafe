# The SOS alert page.
#
# When the student presses the big red button:
#   1. Saves the alert to the database
#   2. Sends an email to their guardian
#   3. Shows a confirmation with the alert ID

import streamlit as st
from datetime import datetime
from database import save_sos, get_user_sos, resolve_sos
from notify import send_sos_email
from database import get_all_zones

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SOS Alert — CampusSafe",
    page_icon="🆘",
    layout="centered"
)

# ── LOGIN GUARD ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("Please login first.")
    st.stop()

# ── GET LOGGED IN USER ────────────────────────────────────────────────────────
user = st.session_state.user

if not user:
    st.error("Session error: User data not found. Please login again.")
    st.stop()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🆘 SOS Alert")
st.caption("Press the button below to alert your guardian immediately.")
st.write("---")

# ── GUARDIAN CHECK ────────────────────────────────────────────────────────────
# Warn the user if they have no guardian email set
# SOS still works but they should know the email won't send
guardian_email = user.get("guardian_email")

if not guardian_email:
    st.warning(
        "You have not set a guardian email yet. "
        "Go to your Profile page to add one. "
        "SOS will still be saved but no email will be sent."
    )
else:
    st.info(f"📧 Your SOS alert will be sent to: **{guardian_email}**")

st.write(" ")

# ── LOCATION
st.subheader("Where are you right now?")

from ai import find_nearest_zone
st.caption(
    "Click below and allow location access for your exact position"
    "If you skip this, you can, you can select your nearest known location instead"
)
try:
    from streamlit_geolocation import streamlit_geolocation
    location_data  = streamlit_geolocation()

except ImportError:
    location_data = None

use_gps = (
    location_data is not None
    and location_data.get("latitude") is not None
)
if use_gps:
    lat = location_data["latitude"]
    lon = location_data["longitude"]

    nearest = find_nearest_zone(lat,lon)

    st.success(
    f"Using your real-time location"
    f"(near **{nearest['name'] if nearest else 'campus'}**)"
    )
    st.caption(f"Exact coordinates: {lat:.5f},{lon:.5f}")
    location_label = (
    f"near {nearest['name']}" if nearest else "current location"
    )

else:
    st.info("GPS not available. Select your nearest campus location instead")

    zones     = get_all_zones()
    zone_names = [z["name"] for z in zones]

    selected_zone = st.selectbox(
    "Select your nearest campus location",
    zone_names,
    help="This helps your guardian find you faster"
    )

    # Get coordinates of the selected zone
    selected_zone_data = next(
    (z for z in zones if z["name"] == selected_zone),
    None
    )

    if selected_zone_data:
        lat = selected_zone_data["latitude"]
        lon = selected_zone_data["longitude"]
    else:
        # Fallback to center of DAVV if zone not found
        lat = 22.6810
        lon = 75.8800

    location_label = selected_zone

st.write(" ")

# ── SOS BUTTON ────────────────────────────────────────────────────────────────
st.subheader("Emergency Alert")

# Show what will happen before the button is pressed
st.write(
    "Pressing SOS will:\n"
    "- Save an alert to the database\n"
    "- Email your guardian with your location\n"
    "- Show a confirmation with your alert ID"
)

st.write(" ")

# The actual SOS button
# We use a session state flag to prevent double-sending
# if the user clicks twice quickly
if "sos_sent" not in st.session_state:
    st.session_state.sos_sent = False

# Large red button using custom styling
sos_pressed = st.button(
    "🆘 SEND SOS ALERT",
    use_container_width=True,
    type="primary",          # makes it the accent color
    key="sos_button"
)

if sos_pressed and not st.session_state.sos_sent:

    st.session_state.sos_sent = True

    with st.spinner("Sending SOS alert..."):

        # ── Step 1: Save to database ──────────────────────────────────────────
        alert_id = save_sos(
            user_id   = user["id"],
            user_name = user["name"],
            latitude  = lat,
            longitude = lon
        )

        # ── Step 2: Send email to guardian ────────────────────────────────────
        email_sent = False
        email_message = ""
        if guardian_email:
            email_sent, email_message = send_sos_email(
                guardian_email = guardian_email,
                student_name   = user["name"],
                latitude       = lat,
                longitude      = lon
            )

    # ── Step 3: Show confirmation ─────────────────────────────────────────────
    st.write(" ")
    st.error("🚨 SOS ALERT SENT")

    # Show details in a clean layout
    my_alert_count = len(get_user_sos(user["id"]))

    col1, col2 = st.columns(2)
    col1.metric("Your Alert #", my_alert_count)
    col2.metric("Time",
                datetime.now().strftime("%I:%M %p"))

    st.write(" ")

    if email_sent:
        st.success(f"✅ Email sent to {guardian_email}")
    elif guardian_email:
        st.warning(f"⚠️ Email could not be sent: {email_message}")
    else:
        st.warning("No guardian email set — alert saved to database only")

    # Google Maps link so guardian can navigate
    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    st.markdown(f"📍 [Open your location on Google Maps]({maps_link})")

    st.write(" ")
    st.info(
        "**Stay where you are if safe to do so.**\n\n"
        "Emergency numbers:\n"
        "- Police: **100**\n"
        "- Women Helpline: **1090**"
    )

    # Reset button so they can send another SOS if needed
    if st.button("Send Another SOS", key="reset_sos"):
        st.session_state.sos_sent = False
        st.rerun()


# ── MY ALERT HISTORY ─────────────────────────────────────────────────────────
st.write("---")
st.subheader("My SOS History")

my_alerts = get_user_sos(user["id"])

if not my_alerts:
    st.caption("No SOS alerts yet. Stay safe!")

else:
    for i, alert in enumerate(my_alerts, start = 1):

        # Color the status badge
        if alert["status"] == "active":
            status_color = "🔴"
        else:
            status_color = "🟢"

        # Show each alert as an expandable section
        with st.expander(
            f"{status_color} Your Alert #{i} — "
            f"{alert['triggered_at']}"
        ):
            col1, col2 = st.columns(2)
            col1.write(f"**Status:** {alert['status'].capitalize()}")
            col2.write(f"**Location:** {alert['latitude']}, "
                       f"{alert['longitude']}")

            maps_link = (f"https://maps.google.com/?"
                         f"q={alert['latitude']},{alert['longitude']}")
            st.markdown(f"[📍 View on Google Maps]({maps_link})")

            # Admin or the same user can mark alert as resolved
            if alert["status"] == "active":
                if st.button("Mark as Resolved",
                             key=f"resolve_{alert['id']}"):
                    resolve_sos(alert["id"])
                    st.success("Marked as resolved.")
                    st.rerun()
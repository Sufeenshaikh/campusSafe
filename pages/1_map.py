import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
from database import get_all_zones

#PAGE CONFIG
st.set_page_config(
    page_title="Safety Map — CampusSafe",
    page_icon="🗺️",
    layout="wide" 
)

# ── LOGIN GUARD
# no one can open URL directly without logging in
# if not st.session_state.get("logged_in"):
#     st.warning("Please login first")
#     st.stop()
    # st.stop() immediately stops the rest of the page from running.
    # Nothing below this line runs if the user is not logged in.

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🗺️ Campus Safety Map")
st.caption("Live safety zones for DAVV Indore. "
           "Colors update automatically from student reports.")
st.write("---")

# Show what the colors mean before the map loads
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
col1.success("🟢 Safe")
col2.warning("🟡 Caution")
col3.error("🔴 Unsafe")
st.write(" ")


# ── HELPER — COLOR PICKER 
def get_color(safety_level):

    colors = {
        "safe":    "green",
        "caution": "orange",
        "unsafe":  "red"
    }

    # .get(key, default) — returns default if key not found
    return colors.get(safety_level, "blue")

# ── HELPER — ICON PICKER ──────────────────────────────────────────────────────
def get_icon(safety_level):

    icons = {
        "safe":    "check",
        "caution": "exclamation-sign",
        "unsafe":  "remove"
    }
    return icons.get(safety_level, "info-sign")


# ── BUILD THE MAP ─────────────────────────────────────────────────────────────
def build_campus_map(zones):
    campus_map = folium.Map(
        location=[22.6902, 75.8740],
        zoom_start=17,
        tiles="OpenStreetMap"
    )

    # Loop through each zone and add a pin
    for zone in zones:
        color = get_color(zone["safety_level"])
        icon  = get_icon(zone["safety_level"])

        # Build the popup HTML
        # This appears when user clicks the pin
        popup_html = f"""
            <div style="font-family: Arial; min-width: 160px;">
                <h4 style="margin:0 0 6px 0; color:#333;">
                    {zone['name']}
                </h4>
                <p style="margin:0 0 4px 0;">
                    <b>Status:</b>
                    <span style="color:{'green' if zone['safety_level']=='safe'
                                        else 'orange' if zone['safety_level']=='caution'
                                        else 'red'};">
                        {zone['safety_level'].upper()}
                    </span>
                </p>
                <p style="margin:0; color:#666; font-size:12px;">
                    {zone['description']}
                </p>
            </div>
        """

        folium.Marker(
            location = [zone["latitude"], zone["longitude"]],

            # popup = box that appears when you CLICK the pin
            popup = folium.Popup(popup_html, max_width=220),

            # tooltip = text that appears when you HOVER over pin
            tooltip = f"{zone['name']} — {zone['safety_level'].upper()}",

            # icon = the colored pin with a symbol inside
            icon = folium.Icon(
                color  = color,
                icon   = icon,
                prefix = "glyphicon"
            )
        ).add_to(campus_map)

    return campus_map


# ── LOAD ZONES AND RENDER MAP ─────────────────────────────────────────────────
zones = get_all_zones()

if not zones:
    st.error("No zones found in database. "
             "Run init_db() to add default zones.")
    st.stop()

campus_map = build_campus_map(zones)

# st_folium renders the Folium map inside Streamlit
st_folium(
    campus_map,
    width='stretch',
    height=500,
    returned_objects=[]   # we don't need click data back
)

# ── ZONE SUMMARY BELOW MAP ────────────────────────────────────────────────────
st.write("---")

# Count zones by safety level
safe_zones    = [z for z in zones if z["safety_level"] == "safe"]
caution_zones = [z for z in zones if z["safety_level"] == "caution"]
unsafe_zones  = [z for z in zones if z["safety_level"] == "unsafe"]

col1, col2, col3 = st.columns(3)

with col1:
    st.success(f"**Safe Zones ({len(safe_zones)})**")
    for zone in safe_zones:
        st.write(f"🟢 {zone['name']}")
        st.caption(zone['description'])

with col2:
    st.warning(f"**Caution Zones ({len(caution_zones)})**")
    for zone in caution_zones:
        st.write(f"🟡 {zone['name']}")
        st.caption(zone['description'])

with col3:
    st.error(f"**Unsafe Zones ({len(unsafe_zones)})**")
    for zone in unsafe_zones:
        st.write(f"🔴 {zone['name']}")
        st.caption(zone['description'])


# ── TIME BASED SAFETY TIP ─────────────────────────────────────────────────────
st.write("---")
st.subheader("Current Safety Status")

hour = datetime.now().hour

# Tip changes automatically based on current time
if 6 <= hour < 20:
    st.success(
        "☀️ **Daytime** — Most areas are currently safe. "
        "Stay aware of your surroundings."
    )
elif 20 <= hour < 22:
    st.warning(
        "🌆 **Evening** — Be cautious in caution zones. "
        f"Currently {len(unsafe_zones)} zone(s) are marked unsafe. "
        "Avoid isolated areas."
    )
else:
    st.error(
        "🌙 **Night time** — "
        f"{len(unsafe_zones)} unsafe zone(s) active right now. "
        "Travel in groups. Avoid Back Boundary Lane and Old Parking Area. "
        "Keep your guardian informed."
    )

# Show last AI update time if available
zones_with_ai = [z for z in zones if z.get("ai_updated_at")]
if zones_with_ai:
    latest = max(z["ai_updated_at"] for z in zones_with_ai)
    st.caption(f"Map last updated by AI: {latest}")
else:
    st.caption("Map using default safety levels. "
               "Submit reports to activate AI zone updates.")
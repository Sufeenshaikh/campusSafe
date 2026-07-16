import streamlit as st
from database import init_db,register_user,login_user
import streamlit.config as _config

_config.set_option("server.maxMessageSize",200)

init_db()

# ''' set_page_config sets layout, title, icon for the browser '''
# ''' if not pressent : throws error'''

st.set_page_config(
    page_title ="Campus Safe",
    page_icon="🛡️",
    layout = "centered"
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

#AUTH PAGE
def show_auth_page():
    st.title("Campus Safe")
    st.write("Welcome to the campus safety app")
    st.write("---")
    
    # ''' st.tabs creates clickable tabs'''
    login_tab, register_tab = st.tabs(["Login","Register"])
    
    #LOGIN TAB
    with login_tab:
        st.subheader("Welcome Back")
        st.write(" ")

        # '''key binds it to state session creating memory'''
        email = st.text_input("Email",key = "login_email")
        password = st.text_input("Password",type = "password",key = "login_pass")

        if st.button("Login", width='stretch'):
            if email.strip() and password.strip():
                 user = login_user(email,password)
                 if user:
                     st.session_state["logged_in"] = True
                     st.session_state.user = {
                         "id": user["id"],
                         "name": user["name"],
                         "email": user["email"],
                         "role": user["role"],
                         "guardian_email": user["guardian_email"]
                        
                     }
                     st.rerun()
                 else:
                     st.error("Invalid email or password")
            else:
                st.error("Please enter both email and password")


                

    #REGISTER TAB
    with register_tab:
        st.subheader("Create your Account")

        reg_name = st.text_input("Full Nname", key = "reg_name")
        reg_email = st.text_input("Email",key = "reg_email")
        reg_password = st.text_input("Password",type = "password", key = "reg_pass")
        reg_guardian = st.text_input("Guardian email",key = "reg_guardian",help = "This person will recieve your SOS alerts")

        reg_role = st.selectbox("role:",["Student","Admin"],key = "reg_role")

        if st.button("Create Account", width='stretch', key = "register_btn"):
        
             if not all([reg_name, reg_email, reg_password, reg_guardian]):
                  st.error("Please fill in all fields")
             elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters")

             elif "@" not in reg_email:
                st.error("Please enter a valid email address")
             else:
                 # Try to save to database
                success = register_user(
                    name           = reg_name,
                    email          = reg_email,
                    password       = reg_password,
                    guardian_email = reg_guardian,
                    role           = reg_role.lower()
                )

                if success:
                    st.success("Account created! You can now login.")
                else:
                    st.error("This email is already registered.")
            

#HOME PAGE
def show_home_page():

    from database import get_all_zones, get_recent_reports, get_all_sos
    user  = st.session_state.user

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("🛡️ CampusSafe")
    st.write(f"Welcome, **{user['name']}** 👋")
    st.caption(f"Role: {user['role'].capitalize()}  |  "
               f"Guardian: {user.get('guardian_email', 'Not set')}")
    st.write("---")

    # ── Live stats ────────────────────────────────────────────────────────────
    # Three numbers at the top — updates every time page loads
    zones        = get_all_zones()
    reports      = get_recent_reports(days=7)
    active_sos   = [s for s in get_all_sos() if s["status"] == "active"]
    unsafe_count = sum(1 for z in zones if z["safety_level"] == "unsafe")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label = "Unsafe Zones",
            value = unsafe_count,
            help  = "Zones currently marked unsafe on campus"
        )

    with col2:
        st.metric(
            label = "Reports (7 days)",
            value = len(reports),
            help  = "Incident reports in the last 7 days"
        )

    with col3:
        st.metric(
            label = "Active SOS",
            value = len(active_sos),
            help  = "SOS alerts currently marked active"
        )

    st.write("---")

    # ── Time based safety tip ─────────────────────────────────────────────────
    from datetime import datetime
    hour = datetime.now().hour

    if 6 <= hour < 20:
        st.success("☀️ Daytime — most areas are currently safe.")
    elif 20 <= hour < 22:
        st.warning("🌆 Evening — stay in well-lit areas.")
    else:
        st.error("🌙 Night time — avoid isolated zones and travel in groups.")

    st.write("---")
    
    # ── Navigation cards ──────────────────────────────────────────────────────

    st.subheader("Quick Access")
    st.caption("Use the sidebar to navigate between pages")
    st.write(" ")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "**🗺️ Safety Map**\n\n"
            "View live campus safety zones with color-coded markers"
        )
        st.info(
            "**📝 Report Incident**\n\n"
            "Submit a safety report — AI auto-scores the severity"
        )
    
    with col2:
        st.error(
            "**🆘 SOS Alert**\n\n"
            "Press SOS to alert your guardian instantly"
        )
        st.info(
            "**🤖 AI Assistant**\n\n"
            "Ask safety questions — powered by Ollama + RAG"
        )

    st.write("---")

# ── Logout ────────────────────────────────────────────────────────────────
    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user      = None
        st.rerun()

if not st.session_state.logged_in:
    show_auth_page()
else:
    show_home_page()
        


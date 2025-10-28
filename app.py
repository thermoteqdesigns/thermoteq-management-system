# ==========================================================
# Thermoteq Management System (TMS)
# Main Entry Point: app.py
# Author: Thermoteq Technologies
# ==========================================================

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

# ==========================================================
# --- PAGE CONFIGURATION ---
# ==========================================================
st.set_page_config(
    page_title="Thermoteq Management System",
    page_icon="🔥",
    layout="wide"
)

# ==========================================================
# --- LOAD CONFIGURATION FILE (Users + Cookies) ---
# ==========================================================
CONFIG_PATH = Path("config/config.yaml")

if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as file:
        config = yaml.load(file, Loader=SafeLoader)
else:
    st.error("Configuration file missing! Please add config/config.yaml.")
    st.stop()

# ==========================================================
# --- AUTHENTICATION SETUP ---
# ==========================================================
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized', [])
)

# ==========================================================
# --- LOGIN SCREEN & ADMIN ROLE HANDLING ---
# ==========================================================
authenticator.login("main", "Login")

# Get authentication status
auth_status = st.session_state.get("authentication_status", None)
user_name = st.session_state.get("name", None)
username = st.session_state.get("username", None)

# --- ADMIN ROLE HANDLING ---
if auth_status:
    # Fetch role from YAML config
    credentials = config['credentials']['usernames']  # Correct key
    user_role = credentials.get(username, {}).get('role', 'user')  # Default role = user
    st.session_state["user_role"] = user_role
else:
    st.session_state["user_role"] = None

# ==========================================================
# --- HANDLE AUTHENTICATION STATUS ---
# ==========================================================
if auth_status is False:
    st.error("❌ Username or password is incorrect.")
    st.title("🔐 Thermoteq Management System Login")  # Show login title

elif auth_status is None:
    st.warning("Please enter your username and password.")
    st.title("🔐 Thermoteq Management System Login")  # Show login title before login

elif auth_status:
    # ======================================================
    # --- SIDEBAR NAVIGATION ---
    # ======================================================
    with st.sidebar:
        st.image("assets/thermoteq_logo.jpg", width=180)
        st.title("Thermoteq Management System")
        st.markdown("---")
        st.write(f"👤 Logged in as: **{user_name}**")
        st.write(f"🛡️ Role: **{st.session_state.get('user_role', 'user')}**")

        authenticator.logout("Logout", "sidebar")

        st.markdown("---")
        st.markdown("### 📂 Quick Links")
        st.page_link("pages/File_Manager.py", label="📁 File Manager")
        st.page_link("pages/Prefab_Houses.py", label="🏗️ Prefab Houses")
        st.page_link("pages/Images_Posters.py", label="🖼️ Images & Posters")
        st.page_link("pages/Admin_Panel.py", label="⚙️ Admin Panel")
        st.page_link("pages/Projects.py", label="🧩 My Projects")

    # ======================================================
    # --- MAIN DASHBOARD CONTENT ---
    # ======================================================
    st.title("🔥 Thermoteq Management System")
    st.markdown("Welcome to our central file and project management hub.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 File Manager")
        st.write("Upload, manage, and organize all company documents in one place.")
    with col2:
        st.subheader("🖼️ Images & Posters")
        st.write("Access and manage Thermoteq marketing posters and visuals.")

    st.markdown("---")
    st.info("""
        💡 **Tip:** Use the sidebar to navigate between sections.
        Your uploaded files are stored securely in Google Drive.
    """)

# ==========================================================
# --- FOOTER ---
# ==========================================================
st.markdown("---")
st.caption("© 2025 Thermoteq Technologies | Built with Streamlit 💚")

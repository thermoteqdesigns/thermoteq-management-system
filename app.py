# ==========================================================
# Thermoteq Management System (TMS)
# Main Entry Point: app.py
# Author: Thermoteq Technologies
# ==========================================================

import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import gspread
import os
import json
from google.oauth2.service_account import Credentials

# ==========================================================
# --- PAGE CONFIGURATION ---
# ==========================================================
st.set_page_config(
    page_title="Thermoteq Management System",
    page_icon="🔥",
    layout="wide"
)

# ==========================================================
# --- LOAD USER DATA FROM GOOGLE SHEETS ---
# ==========================================================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID = "1eCXmSX6XkVXeRtfOUHUI74ZOvd9l6IoRCSu9TDP71Ws"
SHEET_NAME = "Sheet1"

try:
    # ✅ Secure credentials handling for Render & local dev
    if "GOOGLE_CREDENTIALS" in os.environ:
        info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = Credentials.from_service_account_info(info, scopes=SCOPE)
    else:
        creds = Credentials.from_service_account_file("keys/tms-service-account.json", scopes=SCOPE)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    users = sheet.get_all_records()

except Exception as e:
    st.error(f"⚠️ Could not connect to Google Sheets: {e}")
    st.stop()

# ==========================================================
# --- CONVERT GOOGLE SHEET DATA TO STREAMLIT FORMAT ---
# ==========================================================
credentials = {"usernames": {}}

for user in users:
    username = user.get("username")
    name = user.get("name", "")
    password = user.get("password", "")
    role = user.get("role", "user")

    if username and password:
        # Detect if password is already hashed
        if not password.startswith("$2"):
            try:
                hashed_password = stauth.Hasher.hash_passwords([password])[0]
            except Exception:
                hashed_password = password
        else:
            hashed_password = password

        credentials["usernames"][username] = {
            "name": name,
            "password": hashed_password,
            "role": role,
        }

# ==========================================================
# --- AUTHENTICATION SETUP ---
# ==========================================================
authenticator = stauth.Authenticate(
    credentials,
    "tms_cookie",
    "abcdef",
    30
)

# ==========================================================
# --- LOGIN FORM & AUTH STATUS ---
# ==========================================================
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

# Only show title + subtitle when NOT logged in
if st.session_state["authentication_status"] in [None, False]:
    # --- LOGIN SCREEN ---
    st.markdown(
        """
        <style>
        .css-18e3th9 {padding-top: 2rem;}
        .css-1d391kg {justify-content: center;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔐 Thermoteq Management System Login")
    st.markdown("Please enter your username and password below to access the system.")
    st.markdown("---")

    # Show login form
    authenticator.login(location="main")

else:
    # Skip title/subtitle entirely if logged in
    authenticator.login(location="main")

# Extract login state
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

# Set user role
if authentication_status:
    user_role = credentials["usernames"].get(username, {}).get("role", "user")
    st.session_state["user_role"] = user_role
else:
    st.session_state["user_role"] = None

# ==========================================================
# --- HIDE SIDEBAR WHEN NOT LOGGED IN ---
# ==========================================================
if authentication_status is None or authentication_status is False:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==========================================================
# --- HANDLE AUTHENTICATION STATUS ---
# ==========================================================
if authentication_status is False:
    st.error("❌ Username or password is incorrect.")

elif authentication_status is None:
    st.info("👆 Please log in using your credentials above.")

else:
    # USER IS LOGGED IN: SHOW SIDEBAR AND DASHBOARD
    with st.sidebar:
        st.image("assets/thermoteq_logo.jpg", width=180)
        st.title("Thermoteq Management System")
        st.markdown("---")
        st.write(f"👤 Logged in as: **{name}**")
        st.write(f"🛡️ Role: **{st.session_state.get('user_role', 'user')}**")

        authenticator.logout("Logout", "sidebar")

        st.markdown("---")
        st.markdown("### 📂 Quick Links")
        st.page_link("pages/File_Manager.py", label="📁 File Manager")
        st.page_link("pages/Prefab_Houses.py", label="🏗️ Prefab Houses")
        st.page_link("pages/Images_Posters.py", label="🖼️ Images & Posters")
        st.page_link("pages/Admin_Panel.py", label="⚙️ Admin Panel")
        st.page_link("pages/Projects.py", label="🧩 My Projects")

    # DASHBOARD CONTENT
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
    st.info(
        """
        💡 **Tip:** Use the sidebar to navigate between sections.
        Your uploaded files are stored securely in Google Drive.
        """
    )

# ==========================================================
# --- FOOTER ---
# ==========================================================
st.markdown("---")
st.caption("© 2025 Thermoteq Technologies | Built with Streamlit 💚")

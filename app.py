# ==========================================================
# Thermoteq Management System (TMS)
# Main Entry Point: app.py
# Modified to load users from PostgreSQL via Supabase
# Uses bcrypt to hash plain-text passwords
# Author: Thermoteq Technologies
# ==========================================================

import os
import streamlit as st
import streamlit_authenticator as stauth
import psycopg2
import psycopg2.extras
import bcrypt

# ==========================================================
# --- PAGE CONFIGURATION ---
# ==========================================================
st.set_page_config(
    page_title="Thermoteq Management System",
    page_icon="🔥",
    layout="wide"
)

# ==========================================================
# --- LOAD USERS FROM DATABASE ---
# ==========================================================
def load_users_from_db():
    try:
        # Read the full connection string from environment variable
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            st.error("⚠️ DATABASE_URL environment variable not set.")
            st.stop()

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Only select columns that exist
        cur.execute("""
            SELECT
                username,
                password_hash,
                role
            FROM users;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"⚠️ Could not connect to PostgreSQL: {e}")
        st.stop()

db_users = load_users_from_db()

# ==========================================================
# --- CONVERT DB DATA TO STREAMLIT-AUTHENTICATOR FORMAT ---
# ==========================================================
credentials = {"usernames": {}}
plain_users = []

for row in db_users:
    username = row["username"]
    password = row["password_hash"] or ""
    role = row["role"] or "user"
    name = username  # fallback, since your table has no separate name column

    if username:
        if password.startswith("$2"):  # already hashed
            credentials["usernames"][username] = {
                "name": name,
                "password": password,
                "role": role,
            }
        else:
            # collect plain-text passwords to hash individually
            plain_users.append((username, name, role, password))

# Hash plain-text passwords individually using bcrypt
for username, name, role, plain_password in plain_users:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    credentials["usernames"][username] = {
        "name": name,
        "password": hashed,
        "role": role,
    }

# ==========================================================
# --- AUTHENTICATION SETUP ---
# ==========================================================
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="tms_cookie",
    key=os.environ.get("TMS_COOKIE_KEY", "abcdef"),
    cookie_expiry_days=30
)

# ==========================================================
# --- LOGIN FORM & AUTH STATUS ---
# ==========================================================
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

if st.session_state["authentication_status"] in [None, False]:
    st.markdown("""
        <style>
        .css-18e3th9 {padding-top: 2rem;}
        .css-1d391kg {justify-content: center;}
        </style>
    """, unsafe_allow_html=True)
    st.title("🔐 Thermoteq Management System Login")
    st.markdown("Please enter your username and password below to access the system.")
    st.markdown("---")
    authenticator.login(location="main")
else:
    authenticator.login(location="main")

# Extract login state
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

# Set user role if authenticated
if authentication_status:
    user_role = credentials["usernames"].get(username, {}).get("role", "user")
    st.session_state["user_role"] = user_role
else:
    st.session_state["user_role"] = None

# ==========================================================
# --- HIDE SIDEBAR WHEN NOT LOGGED IN ---
# ==========================================================
if authentication_status in [None, False]:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# ==========================================================
# --- HANDLE AUTH STATUS ---
# ==========================================================
if authentication_status is False:
    st.error("❌ Username or password is incorrect.")
elif authentication_status is None:
    st.info("👆 Please log in using your credentials above.")
else:
    # Sidebar for logged-in users
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

# ==========================================================
# --- DASHBOARD CONTENT ---
# ==========================================================
if authentication_status:
    st.title("🔥 Thermoteq Management System")
    st.markdown("Welcome to our central file and project management hub.")
    
    # Row 1
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 File Manager")
        st.write("Upload, manage, and organize all company documents in one place.")
    with col2:
        st.subheader("🖼️ Images & Posters")
        st.write("Access and manage Thermoteq marketing posters and visuals.")
    
    # Row 2
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🏗️ Prefab Houses")
        st.write("Track and manage prefab housing projects efficiently.")
    with col4:
        st.subheader("🧩 Projects")
        st.write("Monitor ongoing and completed Thermoteq projects with ease.")

    st.markdown("---")
    st.info("💡 **Tip:** Use the sidebar to navigate between sections. Your uploaded files are stored securely in Google Drive.")

# ==========================================================
# --- FOOTER ---
# ==========================================================
st.markdown("---")
st.caption("© 2025 Thermoteq Technologies | Built with Streamlit 💚")

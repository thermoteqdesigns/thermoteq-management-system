import streamlit as st
from pathlib import Path
import shutil
import os
import datetime
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ==========================================================
# --- ADMIN ACCESS CONTROL ---
# ==========================================================
if st.session_state.get("user_role") != "admin":
    st.error("🔒 Access Denied — Admins Only")
    st.stop()

# ==========================================================
# --- PAGE CONFIGURATION ---
# ==========================================================
st.set_page_config(page_title="Thermoteq Admin Panel", layout="wide")
st.title("🛠️ Thermoteq Admin Panel")
st.write("Centralized control for managing projects, files, users, and logs.")
st.markdown("---")

# ==========================================================
# --- SESSION STATE FOR REFRESH ---
# ==========================================================
if "refresh_admin" not in st.session_state:
    st.session_state["refresh_admin"] = False

# ==========================================================
# --- DIRECTORIES ---
# ==========================================================
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
LOG_FILE = Path("logs/admin_logs.txt")
LOG_FILE.parent.mkdir(exist_ok=True)
if not LOG_FILE.exists():
    LOG_FILE.touch()

# ==========================================================
# --- HELPER: LOG ACTIONS ---
# ==========================================================
def log_action(action: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {action}\n")

# ==========================================================
# --- GOOGLE SHEETS CONNECTION ---
# ==========================================================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = "keys/tms-service-account.json"
SHEET_ID = "1eCXmSX6XkVXeRtfOUHUI74ZOvd9l6IoRCSu9TDP71Ws"
SHEET_NAME = "Sheet1"

try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"⚠️ Could not connect to Google Sheets: {e}")
    st.stop()

# ==========================================================
# --- TAB NAVIGATION ---
# ==========================================================
tabs = ["Projects & Files", "Manage Users", "Activity Logs"]
selected_tab = st.sidebar.radio("Admin Panel Sections", tabs)

# ==========================================================
# --- TAB 1: PROJECTS & FILES ---
# ==========================================================
if selected_tab == "Projects & Files":
    st.subheader("📂 Projects & Files Management")

    projects = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    uploaded_files = [f for f in UPLOAD_DIR.iterdir() if f.is_file()]

    st.markdown("### 🏗️ Projects")
    if not projects:
        st.info("No projects available.")
    else:
        for project in projects:
            with st.expander(f"📘 {project.name}", expanded=False):
                st.write(f"**Path:** `{project.resolve()}`")

                # Delete project
                if st.button(f"🗑️ Delete Project", key=f"del_proj_{project.name}"):
                    shutil.rmtree(project)
                    st.success(f"✅ Project '{project.name}' deleted successfully.")
                    log_action(f"Deleted project: {project.name}")
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]

                for folder in ["files", "receipts", "images"]:
                    folder_path = project / folder
                    folder_path.mkdir(exist_ok=True)
                    files = list(folder_path.glob("*"))
                    st.markdown(f"**{folder.capitalize()}**")
                    if not files:
                        st.write("_No files_")
                    else:
                        for f in files:
                            col1, col2 = st.columns([8, 1])
                            with col1:
                                st.write(f.name)
                            with col2:
                                if st.button("🗑️", key=f"del_{project.name}_{f.name}"):
                                    f.unlink()
                                    st.success(f"✅ File '{f.name}' deleted successfully.")
                                    log_action(f"Deleted file: {f.name} in project {project.name}")
                                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]

    st.markdown("### 📁 Uploaded Company Files")
    if not uploaded_files:
        st.info("No uploaded files available.")
    else:
        for f in uploaded_files:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f.name)
            with col2:
                if st.button("🗑️", key=f"del_upload_{f.name}"):
                    f.unlink()
                    st.success(f"✅ File '{f.name}' deleted successfully.")
                    log_action(f"Deleted uploaded file: {f.name}")
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]

# ==========================================================
# --- TAB 2: MANAGE USERS (Google Sheets Integration) ---
# ==========================================================
elif selected_tab == "Manage Users":
    st.subheader("👤 User Management")
    st.markdown("Manage users directly from the connected Google Sheet.")
    st.markdown("---")

    try:
        users = sheet.get_all_records()
        df = pd.DataFrame(users)
    except Exception as e:
        st.error(f"⚠️ Could not load users: {e}")
        df = pd.DataFrame()

    # --- Display Users ---
    st.markdown("### Current Users")
    if df.empty:
        st.info("No users found.")
    else:
        st.dataframe(df)
        st.success(f"✅ {len(df)} users loaded from Google Sheets.")

    # --- Add New User ---
    st.markdown("---")
    st.subheader("➕ Add New User")

    with st.form("add_user_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        submitted = st.form_submit_button("Add User")

        if submitted:
            if new_username and new_name and new_password:
                try:
                    # Check if username exists
                    existing_usernames = [u["username"] for u in users]
                    if new_username in existing_usernames:
                        st.error("❌ Username already exists.")
                    else:
                        new_row = [new_username, new_name, new_password, new_role]
                        sheet.append_row(new_row)
                        st.success(f"✅ User '{new_username}' added successfully!")
                        log_action(f"Added user: {new_username} ({new_role})")
                        st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                except Exception as e:
                    st.error(f"⚠️ Could not add user: {e}")
            else:
                st.error("⚠️ Please fill in all required fields.")

    # --- Delete User ---
    st.markdown("---")
    st.subheader("🗑️ Delete User")

    if not df.empty:
        selected_user = st.selectbox("Select user to delete", df["username"].tolist())
        if st.button("Delete Selected User"):
            try:
                cell = sheet.find(selected_user)
                if cell:
                    sheet.delete_rows(cell.row)
                    st.success(f"✅ User '{selected_user}' deleted successfully.")
                    log_action(f"Deleted user: {selected_user}")
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                else:
                    st.warning("⚠️ User not found in the sheet.")
            except Exception as e:
                st.error(f"⚠️ Could not delete user: {e}")

# ==========================================================
# --- TAB 3: ACTIVITY LOGS ---
# ==========================================================
elif selected_tab == "Activity Logs":
    st.subheader("📜 Admin Activity Logs")

    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        st.info("No logs available yet.")
    else:
        with open(LOG_FILE, "r") as f:
            logs = f.readlines()
        for log in reversed(logs[-100:]):  # show last 100 actions
            st.write(log.strip())

# ==========================================================
# --- PAGE REFRESH ---
# ==========================================================
if st.session_state["refresh_admin"]:
    st.session_state["refresh_admin"] = False
    st.stop()

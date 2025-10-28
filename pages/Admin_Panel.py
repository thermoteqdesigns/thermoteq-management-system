import streamlit as st
from pathlib import Path
import shutil
import yaml
from yaml.loader import SafeLoader
import os
import datetime
import bcrypt

# --- Admin Check ---
if st.session_state.get("user_role") != "admin":
    st.error("🔒 Access Denied — Admins Only")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Thermoteq Admin Panel", layout="wide")
st.title("🛠️ Thermoteq Admin Panel")
st.write("Centralized control for managing projects, files, users, and logs.")

# --- SESSION STATE FOR REFRESH ---
if "refresh_admin" not in st.session_state:
    st.session_state["refresh_admin"] = False

# --- Directories ---
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
LOG_FILE = Path("logs/admin_logs.txt")
LOG_FILE.parent.mkdir(exist_ok=True)
if not LOG_FILE.exists():
    LOG_FILE.touch()

# --- Helper: Log Actions ---
def log_action(action: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {action}\n")

# --- Load Config ---
CONFIG_PATH = Path("config/config.yaml")
if not CONFIG_PATH.exists():
    st.error("Config file missing!")
    st.stop()

with open(CONFIG_PATH) as f:
    config = yaml.load(f, Loader=SafeLoader)

users = config['credentials']['usernames']

# ==========================================================
# --- TAB SELECTION ---
# ==========================================================
tabs = ["Projects & Files", "Manage Users", "Activity Logs"]
selected_tab = st.sidebar.radio("Admin Panel Sections", tabs)

# ==========================================================
# --- TAB 1: Projects & Files ---
# ==========================================================
if selected_tab == "Projects & Files":
    st.subheader("📂 Projects & Files Management")

    # List projects and uploaded files
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

                # List files in subfolders
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
# --- TAB 2: Manage Users ---
# ==========================================================
elif selected_tab == "Manage Users":
    st.subheader("👤 User Management")

    st.markdown("### Current Users")
    for username in list(users.keys()):  # iterate over copy of keys
        info = users[username]
        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            st.write(f"**{info['name']}** ({username}) — Role: {info.get('role','user')}")
        with col2:
            new_role = st.selectbox(
                "Change Role",
                options=["user", "admin"],
                index=0 if info.get("role")=="user" else 1,
                key=f"role_{username}"
            )
            if new_role != info.get("role"):
                users[username]['role'] = new_role
                with open(CONFIG_PATH, "w") as f:
                    yaml.dump(config, f)
                st.success(f"✅ Updated role for {username} to {new_role}")
                log_action(f"Updated role for {username} to {new_role}")
                st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]

        with col3:
            if st.button("🗑️ Delete User", key=f"del_user_{username}"):
                if username == "admin":
                    st.error("❌ Cannot delete default admin.")
                else:
                    del users[username]
                    with open(CONFIG_PATH, "w") as f:
                        yaml.dump(config, f)
                    st.success(f"✅ Deleted user {username}")
                    log_action(f"Deleted user: {username}")
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]

    st.markdown("### ➕ Add New User")
    new_username = st.text_input("Username")
    new_name = st.text_input("Full Name")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"], index=0)

    if st.button("Add User"):
        if new_username and new_name and new_email and new_password:
            if new_username in users:
                st.error("❌ Username already exists.")
            else:
                hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                users[new_username] = {
                    "email": new_email,
                    "name": new_name,
                    "password": hashed_pw,
                    "role": new_role
                }
                with open(CONFIG_PATH, "w") as f:
                    yaml.dump(config, f)
                st.success(f"✅ User '{new_username}' added successfully.")
                log_action(f"Added user: {new_username} with role {new_role}")
                st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
        else:
            st.error("❌ Please fill in all fields.")

# ==========================================================
# --- TAB 3: Activity Logs ---
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
    st.stop()  # triggers a page rerender

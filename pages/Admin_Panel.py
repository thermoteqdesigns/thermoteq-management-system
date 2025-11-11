import streamlit as st
from pathlib import Path
import shutil
import os
import pandas as pd
import psycopg2
import psycopg2.extras
import bcrypt

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
st.write("Centralized control for managing projects, files, and users.")
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

# ==========================================================
# --- POSTGRESQL CONNECTION SETTINGS ---
# ==========================================================
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "thermoteq_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "kahenisatima")  # replace with your password

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ==========================================================
# --- TAB NAVIGATION ---
# ==========================================================
tabs = ["Projects & Files", "Manage Users"]
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
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                    st.rerun()

                # List all files under project folders
                for folder in ["files", "invoices", "purchases", "images"]:
                    folder_path = project / folder
                    folder_path.mkdir(exist_ok=True)
                    files = list(folder_path.glob("*"))
                    st.markdown(f"**{folder.capitalize()}**")
                    if not files:
                        st.write("_No files_")
                    else:
                        for idx, f in enumerate(files):
                            col1, col2 = st.columns([8, 1])
                            with col1:
                                st.write(f.name)
                            with col2:
                                if st.button("🗑️", key=f"del_{project.name}_{folder}_{f.name}_{idx}"):
                                    f.unlink()
                                    st.success(f"✅ File '{f.name}' deleted successfully.")
                                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                                    st.rerun()

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
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                    st.rerun()

# ==========================================================
# --- TAB 2: MANAGE USERS (PostgreSQL) ---
# ==========================================================
elif selected_tab == "Manage Users":
    st.subheader("👤 User Management")
    st.markdown("Manage users directly from the PostgreSQL database.")
    st.markdown("---")

    # --- Fetch users from DB ---
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT user_id, username, role, created_at FROM users ORDER BY user_id;")
        users = cur.fetchall()
        df = pd.DataFrame(users, columns=["user_id", "username", "role", "created_at"])
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Could not fetch users: {e}")
        df = pd.DataFrame()

    # --- Display Users ---
    st.markdown("### Current Users")
    if df.empty:
        st.info("No users found.")
    else:
        st.dataframe(df)
        st.success(f"✅ {len(df)} users loaded from database.")

    # --- Add New User ---
    st.markdown("---")
    st.subheader("➕ Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        submitted = st.form_submit_button("Add User")

        if submitted:
            if new_username and new_password:
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT username FROM users WHERE username=%s;", (new_username,))
                    if cur.fetchone():
                        st.error("❌ Username already exists.")
                    else:
                        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                        cur.execute(
                            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s);",
                            (new_username, hashed, new_role)
                        )
                        conn.commit()
                        st.success(f"✅ User '{new_username}' added successfully!")
                    cur.close()
                    conn.close()
                    st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Could not add user: {e}")
            else:
                st.error("⚠️ Please fill in all required fields.")

    # --- Update User ---
    st.markdown("---")
    st.subheader("✏️ Update User")
    if not df.empty:
        selected_user = st.selectbox("Select user to update", df["username"].tolist())
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        new_role = st.selectbox("New Role", ["user", "admin"], index=0)
        if st.button("Update User"):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                # Update password only if provided
                if new_password:
                    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                    cur.execute("UPDATE users SET password_hash=%s, role=%s WHERE username=%s;", 
                                (hashed, new_role, selected_user))
                else:
                    cur.execute("UPDATE users SET role=%s WHERE username=%s;", 
                                (new_role, selected_user))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ User '{selected_user}' updated successfully!")
                st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Could not update user: {e}")

    # --- Delete User ---
    st.markdown("---")
    st.subheader("🗑️ Delete User")
    if not df.empty:
        selected_user = st.selectbox("Select user to delete", df["username"].tolist(), key="delete_user")
        if st.button("Delete Selected User"):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE username=%s;", (selected_user,))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ User '{selected_user}' deleted successfully.")
                st.session_state["refresh_admin"] = not st.session_state["refresh_admin"]
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Could not delete user: {e}")

# ==========================================================
# --- PAGE REFRESH ---
# ==========================================================
if st.session_state["refresh_admin"]:
    st.session_state["refresh_admin"] = False
    st.stop()

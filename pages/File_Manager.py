import streamlit as st
from pathlib import Path
import psycopg2
import psycopg2.extras
import base64
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Thermoteq File Manager", layout="wide")
st.title("📁 Thermoteq File Manager")
st.write("Upload, preview, and manage your files securely.")

# --- DATABASE CONNECTION ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "thermoteq_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "kahenisatima")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# --- SESSION STATE ---
if "preview_file_id" not in st.session_state:
    st.session_state["preview_file_id"] = None
if "last_viewed_file_id" not in st.session_state:
    st.session_state["last_viewed_file_id"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "user"
if "user_id" not in st.session_state:
    st.session_state["user_id"] = 1
if "uploaded" not in st.session_state:
    st.session_state["uploaded"] = False

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --- UPLOAD MODE --- (Always on Top)
st.markdown("### 📤 Upload File")
uploaded_file = st.file_uploader(
    "Select a file", type=["pdf", "docx", "xlsx", "txt", "csv"], key="upload"
)

if uploaded_file and not st.session_state["uploaded"]:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{uploaded_file.name}"
    save_path = UPLOAD_DIR / unique_filename

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO files (file_name, file_path, uploaded_by) VALUES (%s, %s, %s) RETURNING file_id;",
            (uploaded_file.name, str(save_path), st.session_state["user_id"])
        )
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"✅ '{uploaded_file.name}' uploaded successfully!")
        st.session_state["uploaded"] = True
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not save file to database: {e}")

# --- FILE PREVIEW MODE ---
if st.session_state["preview_file_id"]:
    file_id = st.session_state["preview_file_id"]
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT file_name, file_path FROM files WHERE file_id=%s;", (file_id,))
        file_data = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Could not fetch file: {e}")
        st.stop()

    if not file_data:
        st.error("❌ File not found in database.")
        st.session_state["preview_file_id"] = None
        st.rerun()

    file_name = file_data["file_name"]
    file_path = Path(file_data["file_path"])

    st.subheader(f"📄 Preview: {file_name}")

    if st.button("⬅️ Back to File List"):
        st.session_state["last_viewed_file_id"] = file_id
        st.session_state["preview_file_id"] = None
        st.rerun()

    if not file_path.exists():
        st.warning("⚠️ File is missing on disk.")
    else:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                b64_pdf = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="800px" style="border:none;"></iframe>',
                unsafe_allow_html=True
            )
        elif ext in [".jpg", ".jpeg", ".png"]:
            st.image(file_path, use_container_width=True)
        else:
            st.download_button("📥 Download File", file_path.open("rb"), file_name=file_name)

# --- LIST FILES --- (Show ONLY when NOT in preview mode)
if not st.session_state["preview_file_id"]:
    st.markdown("### 📄 Existing Files")
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT file_id, file_name, file_path, uploaded_at FROM files ORDER BY uploaded_at DESC;")
        files = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Could not fetch files from database: {e}")
        files = []

    if files:
        for file in files:
            file_path = Path(file["file_path"])
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                # Highlight only after clicking back
                if file["file_id"] == st.session_state.get("last_viewed_file_id"):
                    st.markdown(f"<span style='color:red; font-weight:bold;'>📎 {file['file_name']}</span>", unsafe_allow_html=True)
                else:
                    st.write(f"📎 {file['file_name']}")
            with col2:
                if file_path.exists():
                    if st.button("👁️ View", key=f"view_{file['file_id']}"):
                        st.session_state["preview_file_id"] = file["file_id"]
                        st.rerun()
                else:
                    st.warning("⚠️ File missing")
            with col3:
                if file_path.exists():
                    with file_path.open("rb") as f:
                        st.download_button("📥", f, file_name=file["file_name"], key=f"download_{file['file_id']}")
                else:
                    st.warning("⚠️ Missing")
            with col4:
                if st.button("🗑️ Delete", key=f"delete_{file['file_id']}"):
                    try:
                        # Delete from disk
                        if file_path.exists():
                            file_path.unlink()
                        # Delete from database
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM files WHERE file_id=%s;", (file["file_id"],))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"✅ '{file['file_name']}' deleted successfully.")

                        # Reset uploaded flag and preview/last viewed states if needed
                        st.session_state["uploaded"] = False
                        if st.session_state.get("preview_file_id") == file["file_id"]:
                            st.session_state["preview_file_id"] = None
                        if st.session_state.get("last_viewed_file_id") == file["file_id"]:
                            st.session_state["last_viewed_file_id"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Could not delete file: {e}")
    else:
        st.info("No files uploaded yet.")

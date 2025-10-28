import streamlit as st
from pathlib import Path
import os
import base64

# --- Page Config ---
st.set_page_config(page_title="Thermoteq File Manager", layout="wide")

# ==========================================================
# --- SESSION STATE SETUP ---
# ==========================================================
if "view_file_name" not in st.session_state:
    st.session_state["view_file_name"] = None
if "selected_files" not in st.session_state:
    st.session_state["selected_files"] = set()
if "sort_by" not in st.session_state:
    st.session_state["sort_by"] = "Name"
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "user"  # default role; set to 'admin' during login
if "refresh_files" not in st.session_state:
    st.session_state["refresh_files"] = False

# ==========================================================
# --- UPLOAD DIRECTORY ---
# ==========================================================
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ==========================================================
# --- PAGE TITLE ---
# ==========================================================
st.title("📁 Thermoteq File Manager")
st.write("Upload, view, and download your files securely and easily.")

# ==========================================================
# --- FILE UPLOADER ---
# ==========================================================
st.markdown("### 📤 Upload Document")
uploaded_file = st.file_uploader(
    "Upload your file",
    type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx"],
)
if uploaded_file:
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ {uploaded_file.name} uploaded successfully.")
    st.experimental_rerun()  # refresh page to show new file

# ==========================================================
# --- GET ALL FILES ---
# ==========================================================
files = list(UPLOAD_DIR.iterdir())

# ==========================================================
# --- SEARCH / FILTER / SORT ---
# ==========================================================
st.markdown("### 🔍 Search, Filter & Sort Files")
search_text = st.text_input("Search by file name")
file_type_filter = st.selectbox("Filter by file type", ["All", "PDF", "Image", "Word", "Excel"])
sort_by = st.selectbox("Sort by", ["Name", "Type", "Date"])
st.session_state["sort_by"] = sort_by

# Map filter to extensions
type_map = {
    "PDF": [".pdf"],
    "Image": [".jpg", ".jpeg", ".png"],
    "Word": [".docx"],
    "Excel": [".xlsx"]
}

# Filter files
filtered_files = []
for file in files:
    ext = file.suffix.lower()
    matches_search = search_text.lower() in file.name.lower()
    matches_type = True if file_type_filter == "All" else ext in type_map[file_type_filter]
    if matches_search and matches_type:
        filtered_files.append(file)

# Sort files
if sort_by == "Name":
    filtered_files.sort(key=lambda f: f.name.lower())
elif sort_by == "Type":
    filtered_files.sort(key=lambda f: f.suffix.lower())
elif sort_by == "Date":
    filtered_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

# ==========================================================
# --- DISPLAY FILES ---
# ==========================================================
st.markdown("### 📄 Files")

if not filtered_files:
    st.info("No files match your search/filter.")
else:
    for file in filtered_files:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])  # added extra column for delete button

        # --- FILE NAME ---
        with col1:
            st.write(f"📎 **{file.name}**")

        # --- VIEW BUTTON ---
        with col2:
            if st.button("👁️ View", key=f"view_{file.name}"):
                st.session_state["view_file_name"] = file.name
                st.experimental_rerun()

        # --- DOWNLOAD BUTTON ---
        with col3:
            with open(file, "rb") as f:
                st.download_button(
                    label="📥 Download",
                    data=f,
                    file_name=file.name,
                    mime="application/octet-stream",
                    key=f"download_{file.name}",
                )

        # --- DELETE BUTTON (admins only) ---
        with col4:
            if st.session_state.get("user_role") == "admin":
                if st.button("🗑️ Delete", key=f"delete_{file.name}"):
                    try:
                        file.unlink()
                        st.success(f"✅ File '{file.name}' deleted successfully!")
                        st.session_state["refresh_files"] = not st.session_state["refresh_files"]
                    except Exception as e:
                        st.error(f"❌ Failed to delete '{file.name}': {e}")

# --- Trigger page refresh for admin deletion ---
if st.session_state["refresh_files"]:
    st.experimental_rerun()

# ==========================================================
# --- DISPLAY SELECTED FILE SIDE-BY-SIDE ---
# ==========================================================
if st.session_state["view_file_name"]:
    file_name = st.session_state["view_file_name"]
    file_path = UPLOAD_DIR / file_name

    if not file_path.exists():
        st.error(f"❌ File '{file_name}' not found.")
    else:
        st.markdown("---")
        st.title(f"📄 Viewing: {file_name}")

        # --- Back Button ---
        if st.button("⬅️ Back to File Manager"):
            st.session_state["view_file_name"] = None
            st.experimental_rerun()

        file_ext = file_path.suffix.lower()
        left_col, right_col = st.columns([2, 5])  # side-by-side preview

        # Preview in right column
        with right_col:
            if file_ext == ".pdf":
                with open(file_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode("utf-8")
                pdf_display = f"""
                    <iframe 
                        src="data:application/pdf;base64,{base64_pdf}" 
                        width="100%" 
                        height="900px"
                        style="border:none;"
                        type="application/pdf">
                    </iframe>
                """
                st.markdown(pdf_display, unsafe_allow_html=True)
            elif file_ext in [".jpg", ".jpeg", ".png"]:
                st.image(str(file_path), use_container_width=True)
            else:
                st.warning("⚠️ Preview not supported for this file type.")
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="📥 Download File",
                        data=f,
                        file_name=file_name,
                        mime="application/octet-stream"
                    )

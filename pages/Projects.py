import streamlit as st
from pathlib import Path
import shutil
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="Thermoteq Projects", layout="wide")

# --- PAGE TITLE ---
st.title("📂 Thermoteq Projects")
st.write("Manage, track, and organize all your projects in one place.")

# --- PROJECTS DIRECTORY ---
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

# --- SESSION STATE ---
for key in [
    "view_file_path",
    "view_project_name",
    "scroll_to_file",
    "expand_project",
    "highlight_file",
    "project_order",
]:
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state["project_order"] is None:
    st.session_state["project_order"] = [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]

# ==========================================================
# --- DISPLAY SELECTED FILE (VIEW MODE) ---
# ==========================================================
if st.session_state["view_file_path"]:
    file_path = Path(st.session_state["view_file_path"])
    project_name = st.session_state.get("view_project_name", "Projects")

    if not file_path.exists():
        st.error(f"❌ File not found: {file_path}")
        st.session_state["view_file_path"] = None
        st.rerun()
    else:
        st.markdown("---")
        st.title(f"📄 Viewing: {file_path.name}")

        if st.button("⬅️ Back to file location"):
            st.session_state["scroll_to_file"] = file_path.name
            st.session_state["expand_project"] = project_name
            st.session_state["highlight_file"] = file_path.name
            st.session_state["view_file_path"] = None
            st.rerun()

        ext = file_path.suffix.lower()
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(f"""
                <iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=1" width="100%" height="750px" style="border:none;"></iframe>
            """, unsafe_allow_html=True)
        elif ext in [".jpg", ".jpeg", ".png"]:
            st.image(str(file_path), use_container_width=True)
        elif ext in [".txt", ".py", ".csv", ".log"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            st.text_area("File Content", content, height=400)
        else:
            st.warning("⚠️ Preview not supported for this file type.")
            with open(file_path, "rb") as f:
                st.download_button(label="📥 Download File", data=f, file_name=file_path.name, mime="application/octet-stream")

        st.stop()

# ==========================================================
# --- ADD NEW PROJECT ---
# ==========================================================
st.subheader("➕ Create a New Project")
project_name_input = st.text_input("Enter project name")

if st.button("Create Project"):
    if project_name_input.strip():
        project_path = PROJECTS_DIR / project_name_input.strip()
        if not project_path.exists():
            for folder in ["files", "receipts", "images"]:
                (project_path / folder).mkdir(parents=True, exist_ok=True)
            st.success(f"✅ Project **{project_name_input}** created successfully.")
            st.rerun()
        else:
            st.warning("⚠️ A project with that name already exists.")
    else:
        st.error("❌ Please enter a valid project name.")

# ==========================================================
# --- REORDER PROJECTS ---
# ==========================================================
expanded_project = st.session_state.get("expand_project")
if expanded_project and expanded_project in st.session_state["project_order"]:
    st.session_state["project_order"].remove(expanded_project)
    st.session_state["project_order"].insert(0, expanded_project)

projects_ordered = []
for name in st.session_state["project_order"]:
    path = PROJECTS_DIR / name
    if path.exists() and path.is_dir():
        projects_ordered.append(path)
for p in PROJECTS_DIR.iterdir():
    if p.is_dir() and p not in projects_ordered:
        projects_ordered.append(p)
        st.session_state["project_order"].append(p.name)

# ==========================================================
# --- SEARCH / FILTER PROJECTS ---
# ==========================================================
st.subheader("🔍 Search / Filter Projects")
search_query = st.text_input("Search projects by name").strip().lower()
if search_query:
    projects_ordered = [p for p in projects_ordered if search_query in p.name.lower()]
    if not projects_ordered:
        st.info("No projects match your search.")

st.markdown("### 📁 Existing Projects")

if not projects_ordered:
    st.info("No projects available yet.")
else:
    for project in projects_ordered:
        for folder in ["files", "receipts", "images"]:
            (project / folder).mkdir(exist_ok=True)

        expanded_state = st.session_state.get("expand_project") == project.name

        with st.expander(f"📘 Open Project: {project.name}", expanded=expanded_state):
            st.write(f"**Path:** `{project.resolve()}`")
            st.markdown("---")

            # --- UPLOAD FILES ---
            st.markdown("#### 🧰 Upload Files")
            col1, col2, col3 = st.columns(3)
            with col1:
                file_to_upload = st.file_uploader(f"Add File to {project.name}", type=["pdf", "docx", "xlsx"], key=f"file_{project.name}")
                if file_to_upload:
                    save_path = project / "files" / file_to_upload.name
                    with open(save_path, "wb") as f:
                        f.write(file_to_upload.getbuffer())
                    st.success(f"📁 File '{file_to_upload.name}' added to {project.name}")
                    st.rerun()
            with col2:
                receipt_to_upload = st.file_uploader(f"Add Receipt to {project.name}", type=["pdf", "jpg", "jpeg", "png"], key=f"receipt_{project.name}")
                if receipt_to_upload:
                    save_path = project / "receipts" / receipt_to_upload.name
                    with open(save_path, "wb") as f:
                        f.write(receipt_to_upload.getbuffer())
                    st.success(f"🧾 Receipt '{receipt_to_upload.name}' added to {project.name}")
                    st.rerun()
            with col3:
                image_to_upload = st.file_uploader(f"Add Image to {project.name}", type=["jpg", "jpeg", "png"], key=f"image_{project.name}")
                if image_to_upload:
                    save_path = project / "images" / image_to_upload.name
                    with open(save_path, "wb") as f:
                        f.write(image_to_upload.getbuffer())
                    st.success(f"🖼️ Image '{image_to_upload.name}' added to {project.name}")
                    st.rerun()

            st.markdown("---")

            # --- VIEW & DOWNLOAD FILES ---
            st.markdown("### 👁️ View & Download Files")

            def list_files(folder_path, label):
                files = list(folder_path.glob("*"))
                st.markdown(f"#### {label}")
                if not files:
                    st.caption(f"No {label.lower()} available yet.")
                else:
                    for file in files:
                        is_highlighted = file.name == st.session_state.get("highlight_file")
                        highlight_style = "background-color: #F61111FF; padding:4px; border-radius:6px;" if is_highlighted else ""

                        col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
                        with col1:
                            st.markdown(f"<div style='{highlight_style}'>📄 {file.name}</div>", unsafe_allow_html=True)
                        with col2:
                            if st.button("👁️ View", key=f"view_{file}_{label}"):
                                st.session_state["view_file_path"] = str(file)
                                st.session_state["view_project_name"] = project.name
                                st.session_state["expand_project"] = project.name
                                st.session_state["highlight_file"] = file.name
                                st.rerun()
                        with col3:
                            with open(file, "rb") as f:
                                st.download_button(label="⬇️", data=f, file_name=file.name, mime="application/octet-stream", key=f"download_{file}_{label}")
                        # --- DELETE BUTTON FOR ADMINS ONLY ---
                        with col4:
                            if st.session_state.get("user_role") == "admin":
                                if st.button("🗑️ Delete", key=f"delete_{file}_{label}"):
                                    try:
                                        file.unlink()
                                        st.success(f"✅ Deleted '{file.name}' successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Could not delete '{file.name}': {e}")

            list_files(project / "files", "📁 Files")
            list_files(project / "receipts", "🧾 Receipts")
            list_files(project / "images", "🖼️ Images")

            st.markdown("---")

            # --- DELETE PROJECT FOR ADMINS ONLY ---
            if st.session_state.get("user_role") == "admin":
                if st.button(f"🗑️ Delete Project: {project.name}", key=f"del_{project.name}"):
                    shutil.rmtree(project)
                    st.success(f"✅ Deleted project: {project.name}")
                    st.rerun()
            else:
                st.caption("🔒 Only admins can delete projects.")

st.markdown("---")
st.caption("Thermoteq Project Management • Secure & Organized")

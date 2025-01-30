import streamlit as st
from streamlit_ace import st_ace


def code_editor_view():
    # Initialize session state variables
    if "language" not in st.session_state:
        st.session_state.language = "python"
    if "theme" not in st.session_state:
        st.session_state.theme = "github"
    if "font_size" not in st.session_state:
        st.session_state.font_size = 14
    if "code" not in st.session_state:
        st.session_state.code = ""
    if "output" not in st.session_state:
        st.session_state.output = ""

    with st.expander("⚙️ Customize Editor", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.language = st.selectbox(
                "Language:", ["python", "javascript", "html", "css"], index=0
            )
        with col2:
            st.session_state.theme = st.selectbox(
                "Theme:", ["github","monokai","dracula", "cobalt"], index=0
            )
        with col3:
            st.session_state.font_size = st.slider(
                "Font Size:", min_value=10, max_value=20, value=st.session_state.font_size
            )

    st.markdown("---")
    st.markdown("### ✏️ Write Your Code Below:")
    code = st_ace(
        value=st.session_state.code,
        language=st.session_state.language,
        theme=st.session_state.theme,
        font_size=st.session_state.font_size,
        auto_update=False,
        height=800,
    )
    if code != st.session_state.code:
        st.session_state.code = code
    st.markdown("### 📤 Output:")
    st.code(st.session_state.output, language="text")

    st.markdown("---")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("▶️ Run Code", use_container_width=True):
            run_code()
    with col2:
        st.file_uploader(
            "Upload Code (Optional):",
            type=["txt"],
            help="Upload a .txt file to prefill the editor.",
            key="code_uploader",
        )


def run_code():
    if st.session_state.language == "python":
        try:
            exec_globals = {}
            exec(st.session_state.code, exec_globals)
            st.session_state.output = exec_globals.get("result", "Code executed successfully!")
        except Exception as e:
            st.session_state.output = f"Error: {e}"
    else:
        st.session_state.output = "Code execution is only supported for Python currently."


# Run the code editor
if __name__ == "__main__":
    code_editor_view()

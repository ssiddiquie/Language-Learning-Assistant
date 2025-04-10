import streamlit as st
from main import LanguageLearningAssistant

def set_custom_style():
    st.markdown("""
    <style>
        .stTextInput input {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 8px;
        }
        .stButton button {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 8px 16px;
            background-color: #f8f9fa;
        }
        .chat-message {
            margin: 8px 0;
            padding: 12px;
            border: 1px solid #eee;
            border-radius: 4px;
        }
        .report-section {
            margin: 16px 0;
            padding: 12px;
            border: 1px solid #eee;
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_session():
    if 'assistant' not in st.session_state:
        st.session_state.assistant = LanguageLearningAssistant()
    if 'session_active' not in st.session_state:
        st.session_state.session_active = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def handle_session_toggle():
    if st.session_state.session_active:
        st.session_state.session_active = False
        st.session_state.chat_history = []
        st.session_state.assistant.end_session()
    else:
        if not st.session_state.selected_lang or not st.session_state.selected_level:
            st.warning("Please select language and level first!")
            return
        st.session_state.assistant.start_session(
            st.session_state.selected_lang,
            st.session_state.selected_level
        )
        st.session_state.session_active = True

def main():
    set_custom_style()
    initialize_session()

    st.title("Language Learning Assistant")
    st.subheader("AI-Powered Language Tutor", divider="gray")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.selected_lang = st.selectbox(
            "Choose Language",
            options=["hindi", "spanish", "french", "japanese", "chinese"],
            index=None
        )
    
    with col2:
        st.session_state.selected_level = st.selectbox(
            "Select Level",
            options=["beginner", "intermediate", "expert", "master"],
            index=None
        )

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        btn_label = "End Session" if st.session_state.session_active else "Start Session"
        if st.button(btn_label, on_click=handle_session_toggle):
            pass

    with col_btn2:
        if st.button("Generate Report", disabled=not st.session_state.session_active):
            st.session_state.report_content = st.session_state.assistant.generate_session_report()

    if st.session_state.session_active:
        user_input = st.chat_input("Type your message...")
        if user_input:
            response = st.session_state.assistant.generate_response(user_input)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("tutor", response))

        for sender, message in st.session_state.chat_history:
            with st.chat_message("user" if sender == "user" else "assistant"):
                st.markdown(f'<div class="chat-message">{message}</div>', unsafe_allow_html=True)

    if 'report_content' in st.session_state:
        st.markdown("---")
        with st.expander("Learning Progress Report"):
            st.markdown(f'<div class="report-section">{st.session_state.report_content}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
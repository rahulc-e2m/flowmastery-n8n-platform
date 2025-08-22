import streamlit as st
import time
from n8n_chatbot import answer_user

# Page configuration
st.set_page_config(
    page_title="n8n Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimalistic design
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .stApp {
        background-color: #0a0a0a;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 3rem;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-top: -2rem;
        margin-bottom: 3rem;
    }
    
    /* Chat container */
    .chat-wrapper {
        max-width: min(1100px, 95vw);
        margin: 0 auto;
        padding: 0 20px;
    }
    
    /* Message styling */
    .message-container {
        margin: 1rem 0;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin-left: auto;
        margin-right: 0;
        max-width: 90%;
        word-wrap: break-word;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .bot-message {
        background-color: #1a1a1a;
        color: #e0e0e0;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin-right: auto;
        margin-left: 0;
        max-width: 90%;
        word-wrap: break-word;
        border: 1px solid #2a2a2a;
        white-space: pre-wrap;
        line-height: 1.6;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 24px !important;
        padding: 12px 20px !important;
        color: #ffffff !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #666 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 24px;
        color: white;
        font-weight: 500;
        padding: 12px 32px;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }
    
    .sidebar .sidebar-content {
        background-color: #0f0f0f;
        color: #e0e0e0;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 2rem 0;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.875rem;
        margin-top: 3rem;
        padding: 2rem 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2a2a2a;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3a3a3a;
    }
    
    /* Message alignment containers */
    .user-message-wrapper {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
    }
    
    .bot-message-wrapper {
        display: flex;
        justify-content: flex-start;
        margin: 1rem 0;
    }
    
    /* Label styling */
    .message-label {
        font-size: 0.75rem;
        color: #666;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }
    
    .user-label {
        text-align: right;
        margin-right: 1rem;
    }
    
    .bot-label {
        text-align: left;
        margin-left: 1rem;
    }

    /* Responsive message widths */
    @media (max-width: 768px) {
        .user-message, .bot-message {
            max-width: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# Sidebar (minimal content)
with st.sidebar:
    st.markdown("## 🤖 n8n Chatbot")
    st.markdown("---")
    
    st.markdown("### About")
    st.markdown("""
    <div style="color: #e0e0e0; font-size: 0.875rem;">
    Interact with your n8n instance using natural language.
    
    <br><br>
    <strong>Capabilities:</strong><br>
    • Query workflows & executions<br>
    • Manage users & tags<br>
    • Access variables & projects<br>
    • Full REST API support
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="color: #666; font-size: 0.75rem; text-align: center;">
    Powered by Gemini AI
    </div>
    """, unsafe_allow_html=True)

# Main content
st.markdown('<h1 class="main-header">n8n Chatbot</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your intelligent n8n assistant</p>', unsafe_allow_html=True)

# Chat interface with wrapper
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

# Chat container
chat_container = st.container()

with chat_container:
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message-wrapper">
                <div>
                    <div class="message-label user-label">You</div>
                    <div class="message-container user-message">{message["content"].lstrip()}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bot-message-wrapper">
                <div>
                    <div class="message-label bot-label">Assistant</div>
                    <div class="message-container bot-message">{message["content"].lstrip()}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Welcome message if no messages
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; color: #666; margin: 4rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">👋</div>
        <div style="font-size: 1.1rem;">Hello! I'm your n8n assistant.</div>
        <div style="font-size: 0.9rem; margin-top: 0.5rem;">
            Ask me anything about your workflows, executions, or n8n configuration.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input area
st.markdown("---")

# Handle clear input
if st.session_state.get("clear_input", False):
    st.session_state.user_input = ""
    st.session_state.clear_input = False

# Input columns
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "Message",
        placeholder="Ask me about workflows, executions, users, or any n8n resource...",
        key="user_input",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send", use_container_width=True, type="primary")

# Handle user input ONLY when Send button is clicked
if send_button and user_input and user_input.strip():
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message immediately
    with chat_container:
        st.markdown(f"""
        <div class="user-message-wrapper">
            <div>
                <div class="message-label user-label">You</div>
                <div class="message-container user-message">{user_input}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Show loading spinner
    with st.spinner(""):
        # Get bot response
        bot_response = answer_user(user_input)

        # Human-like preface referencing the user's query
        final_bot_response = f"Here is what I found for '{user_input.strip()}':\n\n{bot_response.lstrip()}"

        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": final_bot_response})

        # Display bot response
        st.markdown(f"""
        <div class="bot-message-wrapper">
            <div>
                <div class="message-label bot-label">Assistant</div>
                <div class="message-container bot-message">{final_bot_response.lstrip()}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Clear input
    st.session_state.clear_input = True
    st.rerun()

# Footer
st.markdown("""
<div class="footer">
    Built with Streamlit & AI • © 2024
</div>
""", unsafe_allow_html=True)
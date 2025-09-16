import streamlit as st
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize OpenAI client
def initialize_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("Please set your OPENAI_API_KEY in the .env file")
        return None
    
    client = openai.OpenAI(api_key=api_key)
    return client

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "openai_client" not in st.session_state:
    st.session_state.openai_client = initialize_openai()

# Main app
def main():
    st.title("🤖 AI Chat Assistant")
    st.markdown("Ask me anything! I'm here to help with your questions.")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Model selection
        model = st.selectbox(
            "Choose AI Model",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
            index=0
        )
        
        # Temperature setting
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher values make responses more creative, lower values more focused"
        )
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        if st.session_state.openai_client:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Create messages for OpenAI API
                        messages_for_api = [
                            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions."}
                        ] + [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
                        
                        # Get response from OpenAI
                        response = st.session_state.openai_client.chat.completions.create(
                            model=model,
                            messages=messages_for_api,
                            temperature=temperature,
                            max_tokens=1000
                        )
                        
                        ai_response = response.choices[0].message.content
                        
                        # Display AI response
                        st.markdown(ai_response)
                        
                        # Add AI response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        
                    except Exception as e:
                        error_msg = f"Sorry, I encountered an error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.error("OpenAI client not initialized. Please check your API key.")

if __name__ == "__main__":
    main()

# app.py (full code combining all steps)

import os
import openai
import streamlit as st
import io

from dotenv import load_dotenv
import openai
import os
import PyPDF2

load_dotenv()  # Load environment variables from .env

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# If you didn't set an environment variable, you could do:
# client = openai.OpenAI(api_key="sk-your-api-key")  # (Not recommended to hard-code in real apps)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Function to process the uploaded file
def process_uploaded_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        return uploaded_file.getvalue().decode("utf-8")
    else:
        return "Unsupported file type. Please upload a TXT or PDF file."

# Define a function to generate a response from the AI given a user message
def generate_response(user_prompt, file_content=None):
    """
    Sends the user prompt to OpenAI and returns the AI's response.

    Parameters:
    -----------
    user_prompt : str
        The input message from the user.
    file_content : str, optional
        Content extracted from an uploaded file.

    Returns:
    --------
    str
        The AI-generated response as plain text.
    """
    messages = []
    
    # If file content is provided, add it as context
    if file_content:
        messages.append({
            "role": "system", 
            "content": f"The user has uploaded a file with the following content:\n\n{file_content}\n\nPlease consider this information when responding to their query."
        })
    
    # Add the user's prompt
    messages.append({"role": "user", "content": user_prompt})
    
    # Use OpenAI's chat completion endpoint to get a chat-based response
    response = client.chat.completions.create(
        model="gpt-5.4",  # The AI model to use
        messages=messages  # The conversation context
    )
    # Extract the assistant's message from the response
    message_text = response.choices[0].message.content
    return message_text  # Return the assistant's reply



st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 AI Chatbot Assistant")
st.markdown("**Welcome!** Ask anything or upload a file for the bot to analyze.")

# File upload section in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload a file (optional):", type=["txt", "pdf"])
file_content = None

if uploaded_file is not None:
    st.sidebar.write("Uploaded file:", f"**{uploaded_file.name}** ({uploaded_file.size} bytes)")
    
    # Process the file and store its content
    with st.sidebar.spinner("Processing file..."):
        file_content = process_uploaded_file(uploaded_file)
    
    # Show a preview of the file content
    with st.sidebar.expander("File Content Preview"):
        st.write(file_content[:500] + "..." if len(file_content) > 500 else file_content)

if "messages" not in st.session_state:
    st.session_state.messages = []
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm here to help. Feel free to ask me anything or upload a file."})

# Display existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input widget for new messages
if user_msg := st.chat_input("Type your message here..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)
    # Generate assistant response with spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_msg = generate_response(user_msg, file_content)
            st.markdown(assistant_msg)
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
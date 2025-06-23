# app/ui/streamlit_app.py
import streamlit as st
import requests
import os
import json
import time

# Configure the app
st.set_page_config(
    page_title="Agentic LLM Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_id" not in st.session_state:
    st.session_state.file_id = None

# Helper functions
def call_api(endpoint, method="GET", data=None, files=None):
    """Call the backend API."""
    url = f"{API_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            st.error(f"Unsupported method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def upload_file(file):
    """Upload a file to the API."""
    if not file:
        return None
    
    files = {"file": (file.name, file.getvalue(), file.type)}
    response = call_api("api/upload", method="POST", files=files)
    
    if response:
        st.session_state.file_id = response["file_id"]
        return response
    return None

def process_query(query):
    data = {
        "query": query,
        "conversation_id": st.session_state.conversation_id,
        "file_id": st.session_state.file_id
    }
    return call_api("api/chat", method="POST", data=data)

def format_tool_result(tool_name, result):
    """Format tool results for display."""
    if not result or not isinstance(result, dict):
        return "No results available"
    
    # Check if there was an error
    if not result.get("success", True) or "error" in result:
        error_msg = result.get("error", "Unknown error")
        return f"⚠️ Error: {error_msg}"
    
    # Get the actual result data
    result_data = result.get("result", result)
    
    # Format based on tool type
    if tool_name == "web_search":
        return format_web_search_result(result_data)
    elif tool_name == "pdf_parser":
        return format_pdf_result(result_data)
    elif tool_name == "data_analysis":
        return format_data_analysis_result(result_data)
    elif tool_name == "code_execute":  # Changed from code_executor to match main.py
        return format_code_result(result_data)
    else:
        # Generic formatting as JSON
        return f"```json\n{json.dumps(result_data, indent=2)}\n```"

def format_web_search_result(result):
    """Format web search results."""
    if "results" not in result:
        return "No search results found"
    
    formatted = f"**Search Query:** {result.get('query', 'Unknown')}\n\n"
    
    for i, item in enumerate(result["results"], 1):
        formatted += f"{i}. **[{item.get('title', 'No title')}]({item.get('link', '#')})**\n"
        formatted += f"   {item.get('snippet', 'No description')}\n\n"
    
    return formatted

def format_pdf_result(result):
    """Format PDF parsing results."""
    if "metadata" not in result:
        return "No PDF content found"
    
    metadata = result["metadata"]
    formatted = f"**PDF Document**\n"
    formatted += f"Title: {metadata.get('title', 'Untitled')}\n"
    formatted += f"Pages: {metadata.get('total_pages', 0)}\n\n"
    
    if "pages" in result:
        formatted += "**Extracted Content:**\n"
        for page in result["pages"][:2]:  # Show only first 2 pages
            formatted += f"\nPage {page.get('page_number', '?')}:\n"
            text = page.get('text', 'No content')
            # Truncate text if too long
            if len(text) > 500:
                text = text[:500] + "...(content truncated)"
            formatted += f"```\n{text}\n```\n"
        
        if len(result["pages"]) > 2:
            formatted += f"\n... and {len(result['pages']) - 2} more pages"
    
    return formatted

def format_data_analysis_result(result):
    """Format data analysis results."""
    if not result or not isinstance(result, dict):
        return "No analysis results available"
    
    formatted = "**Data Analysis Results**\n\n"
    
    # Handle different operation types
    if "shape" in result:
        rows, cols = result.get("shape", (0, 0))
        formatted += f"Data shape: {rows} rows × {cols} columns\n\n"
    
    if "visualization_type" in result:
        formatted += f"Visualization type: {result['visualization_type']}\n\n"
    
    # If there's sample data, display it
    if "sample" in result or "data" in result:
        data = result.get("sample") or result.get("data")
        if isinstance(data, list) and len(data) > 0:
            formatted += f"Sample data:\n```json\n{json.dumps(data[:5], indent=2)}\n```\n"
    
    # If there's a summary, show it
    if "summary" in result:
        formatted += "\n\nSummary statistics:\n"
        formatted += f"```json\n{json.dumps(result['summary'], indent=2)}\n```\n"
    
    return formatted

def format_code_result(result):
    """Format code execution results."""
    if not result or not isinstance(result, dict):
        return "No code execution results available"
    
    formatted = "**Code Execution Results**\n\n"
    
    # Show execution time
    if "execution_time" in result:
        formatted += f"Execution time: {result['execution_time']:.3f} seconds\n\n"
    
    # Show any errors
    if "error" in result:
        formatted += f"⚠️ Error: {result['error']}\n\n"
        if "traceback" in result:
            formatted += f"```\n{result['traceback']}\n```\n\n"
    
    # Show stdout
    if "stdout" in result and result["stdout"]:
        formatted += "**Output:**\n"
        formatted += f"```\n{result['stdout']}\n```\n\n"
    
    # Show stderr if non-empty and no error already shown
    if "stderr" in result and result["stderr"] and "error" not in result:
        formatted += "**Warnings/Errors:**\n"
        formatted += f"```\n{result['stderr']}\n```\n"
    
    return formatted

# UI Components
def render_header():
    """Render the app header."""
    st.title("🧠 Agentic LLM Platform")
    st.markdown(
        """
        This platform combines multiple AI tools to answer your questions intelligently.
        Ask a question, and the system will automatically use web search, document analysis, 
        data processing, or code execution to provide comprehensive answers.
        """
    )

def render_sidebar():
    """Render the sidebar with settings and tools."""
    st.sidebar.title("Tools & Settings")
    
    # New conversation button
    if st.sidebar.button("New Conversation"):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.file_id = None
        st.rerun()
    
    st.sidebar.subheader("File Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Upload a file for analysis",
        type=["pdf", "csv", "xlsx", "txt", "json"]
    )
    
    if uploaded_file:
        with st.sidebar:
            with st.spinner("Uploading file..."):
                response = upload_file(uploaded_file)
                if response:
                    st.success(f"Uploaded: {uploaded_file.name}")
                    st.info(
                        "You can now ask questions about this file. "
                        "The system will automatically analyze it."
                    )
    
    # Available tools info
    st.sidebar.subheader("Available Tools")
    tools_info = {
        "Web Search": "Finds information online",
        "PDF Parser": "Extracts text from documents",
        "Data Analysis": "Analyzes spreadsheets and data files",
        "Code Executor": "Runs Python code for advanced processing"
    }
    
    for tool, description in tools_info.items():
        st.sidebar.write(f"**{tool}**: {description}")
    
    # Example queries
    st.sidebar.subheader("Example Questions")
    examples = [
        "What are the latest developments in quantum computing?",
        "What is the capital of France?",
        "Who is the current president of the United States?",
        "What is the square root of 14641?"
    ]
    
    for i, example in enumerate(examples):
        if st.sidebar.button(f"Example {i+1}", key=f"example_{i}"):
            st.session_state.messages.append({"role": "user", "content": example})
            process_message(example)
            st.rerun()

def render_chat():
    # 1) 이전 메시지 그리기
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # (도구 결과 렌더링 생략)

    # 2) 사용자 입력받기
    user_input = st.chat_input("Ask a question...")
    if user_input:
        # 3) 사용자 메시지 저장
        st.session_state.messages.append({"role": "user", "content": user_input})
        # 4) 즉시 화면에 출력
        with st.chat_message("user"):
            st.markdown(user_input)
        # 5) 백엔드 호출
        response = process_query(user_input)
        if response:
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["response"],
                "tools_used": response.get("tools_used", []),
                "tool_results": response.get("tool_results", {})
            })
            # 6) 화면에 AI 답변 바로 출력
            with st.chat_message("assistant"):
                st.markdown(response["response"])
                

        
def process_message(prompt):
    """Process a user message and update the UI."""
    # Call API
    response = process_query(prompt)
    
    if response:
        # Extract info
        assistant_response = response["response"]
        tools_used = response.get("tools_used", [])
        tool_results = response.get("tool_results", {})
        
        # Add to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "tools_used": tools_used,
            "tool_results": tool_results
        })
        
        # Display assistant message
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
            
            # Show tool results
            if tools_used:
                with st.expander("View tools used"):
                    for tool in tools_used:
                        st.subheader(f"🛠️ {tool}")
                        if tool in tool_results:
                            st.markdown(format_tool_result(tool, tool_results[tool]))
    else:
        # Handle error
        st.error("Failed to process your query. Please try again.")

# Main app

render_header()
render_sidebar()
render_chat()
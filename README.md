# 🧠 Agentic LLM Platform

An intelligent platform that combines multiple tools like web search, PDF extraction, data analysis, and code execution to answer complex knowledge questions.

## Overview

This project demonstrates advanced AI reasoning and tool orchestration capabilities, similar to systems used in leading AI companies. The platform allows users to interact with a single AI assistant that dynamically selects and combines tools to deliver actionable insights — not just answers.

## Features

- **Multi-Tool Agent Orchestration**: Uses LLMs to select and sequence tools:
  - Web Search API for real-time information
  - PDF document parser for document analysis
  - Data Analysis for CSV/Excel processing
  - Python code execution for custom processing

- **Intelligent Prompt Routing**: Dynamically decides which tools to call based on user intent

- **Memory & Context Handling**: Maintains conversation history for context-aware responses

- **Clean User Interface**: Streamlit-based UI for easy interaction

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for:
  - OpenAI (or other LLM provider)
  - SerpAPI (for web search)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agentic-llm-platform.git
   cd agentic-llm-platform
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   WEB_SEARCH_API_KEY=your_serpapi_key
   ```

### Running the Application

1. Start the API server:
   ```bash
   python run.py
   ```

2. In a new terminal, start the Streamlit UI:
   ```bash
   streamlit run app/ui/streamlit_app.py
   ```

3. Open your browser to `http://localhost:8501`

## Project Structure

```
agentic-llm-platform/
├── app/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── api/
│   │   └── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── web_search.py
│   │   ├── pdf_parser.py
│   │   ├── data_analysis.py
│   │   └── code_executor.py
│   ├── ui/
│   │   └── streamlit_app.py
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── run.py
```

## Usage Examples

- **Web Search**: "What are the latest developments in quantum computing?"
- **PDF Analysis**: "Summarize the key points from this research paper."
- **Data Analysis**: "Analyze this sales data and show me the top performing regions."
- **Code Execution**: "Calculate the correlation between these two variables in my dataset."

## API Endpoints

- `POST /api/chat`: Process a query using the agent
- `POST /api/upload`: Upload a file for analysis
- `GET /api/conversations/{conversation_id}`: Get conversation history
- `DELETE /api/conversations/{conversation_id}`: Delete a conversation
- `DELETE /api/files/{file_id}`: Delete an uploaded file
- `GET /api/health`: Check API health

## Future Improvements

- Add more tools (e.g., image analysis, audio processing)
- Implement more sophisticated memory systems
- Add authentication and user management
- Create a React-based UI alternative
- Deploy as a containerized application on AWS/GCP

## License

[MIT License](LICENSE)

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for inspiration on agent design
- [OpenAI](https://openai.com) for LLM APIs
- [Streamlit](https://streamlit.io) for the UI framework

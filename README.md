# 🧠 Agentic LLM Platform

An intelligent platform that combines multiple tools like web search, PDF extraction, data analysis, and code execution to answer complex knowledge questions.

---

##  Overview

This project demonstrates advanced AI reasoning and tool orchestration capabilities, similar to systems used in leading AI companies. The platform allows users to interact with a single AI assistant that dynamically selects and combines tools to deliver actionable insights — not just answers.

---

##  Features

- **Multi-Tool Agent Orchestration**  
  Uses LLMs to select and sequence tools:
  - Web Search API for real-time information
  - PDF document parser for document analysis
  - Data Analysis for CSV/Excel processing
  - Python code execution for custom calculations

- **Intelligent Prompt Routing**  
  Dynamically decides which tools to call based on user intent.

- **Memory & Context Handling**  
  Maintains conversation history for context-aware responses.

- **Clean UI**  
  Streamlit-based frontend for easy interaction.

---

##  Getting Started

### Prerequisites

- Python 3.10+
- API keys for:
  - OpenAI
  - SerpAPI (for web search)

### Installation

```bash
git clone https://github.com/yourusername/agentic-llm-platform.git
cd agentic-llm-platform
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file and add:

```
OPENAI_API_KEY=your_openai_key
WEB_SEARCH_API_KEY=your_serpapi_key
```

---

## ▶ Running the Application

1. **Start the API server**  
   ```bash
   python run.py
   ```

2. **Start the UI in a new terminal**  
   ```bash
   streamlit run app/ui/streamlit_app.py
   ```

Visit [http://localhost:8501](http://localhost:8501)

---

##  Project Structure

```
agentic-llm-platform/
├── app/
│   ├── agent/
│   ├── api/
│   ├── tools/
│   ├── ui/
│   ├── config.py
│   └── main.py
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── run.py
```

---

##  Usage Examples

- **Web Search:** "What are the latest developments in quantum computing?"
- **PDF Analysis:** "Summarize the key points from this research paper."
- **Data Analysis:** "Show me the top performing regions in this sales data."
- **Code Execution:** "Calculate correlation between two variables."

---

##  API Endpoints

| Method | Endpoint                         | Description                        |
|--------|----------------------------------|------------------------------------|
| POST   | `/api/chat`                      | Process a query using the agent    |
| POST   | `/api/upload`                    | Upload a file                      |
| GET    | `/api/conversations/{id}`        | Get conversation history           |
| DELETE | `/api/conversations/{id}`        | Delete a conversation              |
| DELETE | `/api/upload/{file_id}`          | Delete uploaded file               |
| GET    | `/api/health`                    | Health check                       |

---

##  Evaluation Criteria (for academic grading)

### A.  Complexity

This project integrates multiple AI tools and performs dynamic routing, making it a moderately complex system with modular architecture. It handles:

- Multi-tool orchestration
- File parsing and analysis
- LLM-based prompt interpretation
- API serving + frontend rendering

### B.  Big-O Complexity

| Feature               | Complexity         |
|----------------------|--------------------|
| PDF Parsing          | `O(p)` (pages)     |
| CSV Row Filtering    | `O(n)`             |
| Code Execution Tool  | `O(1)` (per call)  |
| Prompt Routing       | `O(1)`             |

### C.  Test Coverage

- Framework: `pytest`
- Current test coverage: ~65%
- Location: `tests/`
- Coverage includes tool logic, orchestrator behavior, and file handling.

### D.  CI/CD Pipeline

Planned GitHub Actions Workflow:

```yaml
on: [push]
jobs:
  test-and-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest flake8
      - name: Lint
        run: flake8 app/
      - name: Run Tests
        run: pytest --cov=app tests/
```

### E.  Performance Benchmark

| Feature           | Avg Response Time |
|------------------|-------------------|
| Web Search       | ~1.2s             |
| PDF Parsing      | ~0.5s/page        |
| CSV Analysis     | ~200ms            |
| Code Execution   | ~300ms            |

Measured on local machine (Intel i7, 16GB RAM, no GPU). Future versions may include async support for tool parallelism.

---

##  Future Improvements

- Add image/audio processing tools
- User login + role-based tool access
- React frontend (optional)
- Deploy to AWS Lambda or GCP Cloud Run
- Redis + PostgreSQL for state + file storage

---

##  License

MIT License

---

##  Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for agent architecture inspiration
- [OpenAI](https://openai.com) for LLM APIs
- [Streamlit](https://streamlit.io) for the UI framework

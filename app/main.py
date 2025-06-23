import logging
import os
import tempfile
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .config import settings
from .agent.orchestrator import AgentOrchestrator
from .tools.web_search import WebSearchTool
from .tools.pdf_parser import PDFParserTool
from .tools.data_analysis import DataAnalysisTool
from .tools.code_execute import CodeExecuteTool

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="An agentic LLM platform for intelligent knowledge work",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize tools
tools = {
    "web_search": WebSearchTool(),
    "pdf_parser": PDFParserTool(),
    "data_analysis": DataAnalysisTool(),
    "code_execute": CodeExecuteTool(),
}

# Store conversations and uploaded files
conversations: Dict[str, AgentOrchestrator] = {}
uploaded_files: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    file_id: Optional[str] = None

class QueryResponse(BaseModel):
    conversation_id: str
    query: str
    response: str
    tools_used: List[str]
    tool_results: Dict[str, Any]

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str
    size: int

# Helper: get or create orchestrator
def get_orchestrator(conversation_id: Optional[str] = None) -> AgentOrchestrator:
    if conversation_id and conversation_id in conversations:
        return conversations[conversation_id]
    orchestrator = AgentOrchestrator(tools=tools)
    if conversation_id:
        orchestrator.conversation_id = conversation_id
    conversations[orchestrator.conversation_id] = orchestrator
    return orchestrator

# Chat endpoint
@app.post("/api/chat", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        orchestrator = get_orchestrator(request.conversation_id)
        context: Dict[str, Any] = {}
        if request.file_id and request.file_id in uploaded_files:
            context['file_path'] = uploaded_files[request.file_id]['path']
        result = await orchestrator.process_query(request.query, context)
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File upload endpoint
@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            path = tmp.name
        file_id = f"file_{len(uploaded_files) + 1}"
        uploaded_files[file_id] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': len(content),
            'path': path,
        }
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type,
            size=len(content),
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get conversation history
@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    orchestrator = conversations[conversation_id]
    return {"conversation_id": conversation_id, "messages": orchestrator.messages}

# Delete conversation
@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    conversations.pop(conversation_id, None)
    return {"status": "success"}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Cleanup helper
def cleanup_temp_files(file_ids: List[str]):
    for fid in file_ids:
        info = uploaded_files.pop(fid, None)
        if info:
            try:
                os.unlink(info['path'])
            except Exception as e:
                logger.error(f"Error removing file {fid}: {e}")

# Delete file endpoint
@app.delete("/api/upload/{file_id}")
async def delete_file(file_id: str, background_tasks: BackgroundTasks):
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    background_tasks.add_task(cleanup_temp_files, [file_id])
    return {"status": "success"}

# Root
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "description": "An agentic LLM platform for intelligent knowledge work",
        "docs_url": "/docs",
    }

# Run if main
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)

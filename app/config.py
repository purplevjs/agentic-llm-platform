
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # app settings
    APP_NAME = "Agentic LLM Platform"
    DEBUG = True
    API_PREFIX = "/api"
    LOG_LEVEL = "INFO"
    
    # Security settings
    SECRET_KEY = "f68e7d3a1b4c9e2d5f7a8b6c3d2e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440
    
    # LLM settings
    LLM_PROVIDER = "openai"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    
    # Web search settings
    WEB_SEARCH_PROVIDER = "serpapi"
    WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
    WEB_SEARCH_MAX_RESULTS = 5
    WEB_SEARCH_TIMEOUT_SECONDS = 10
    
    # Storage
    STORAGE_PROVIDER = "local"
    LOCAL_STORAGE_PATH = "./storage"
    
    # Tools
    PDF_MAX_PAGES = 50
    PDF_EXTRACTION_MODE = "text_and_tables"
    
    DATA_ANALYSIS_MAX_ROWS = 10000
    DATA_ANALYSIS_ALLOW_WRITE = False
    
    CODE_EXECUTOR_TIMEOUT_SECONDS = 30
    CODE_EXECUTOR_MAX_MEMORY_MB = 512
    CODE_EXECUTOR_ALLOWED_MODULES = "pandas,numpy,matplotlib,seaborn,sklearn,datetime,json,re,math,collections"
    CODE_EXECUTOR_BLOCKED_MODULES = "os,sys,subprocess,socket,requests,urllib,ftplib,telnetlib"
    
    # UI
    UI_THEME = "light"
    UI_HISTORY_LENGTH = 10


settings = Settings()
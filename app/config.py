import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    QDRANT_URL = os.getenv('QDRANT_CLUSTER_ENDPOINT')
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
    QDRANT_COLLECTION = 'Enterprise_RAG'

    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')
    GROQ_FALLBACK_API_KEY = os.getenv('GROQ_FALLBACK_API_KEY')

    PORTKEY_API_KEY = os.getenv('PORTKEY_API_KEY', '')
    GROQ_SLUG = os.getenv('GROQ_SLUG', 'rag')
    GROQ_SLUG_2 = os.getenv('GROQ_SLUG_2', 'brag')

    LOGFIRE_TOKEN = os.getenv('LOGFIRE_TOKEN')
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')


settings = Settings()
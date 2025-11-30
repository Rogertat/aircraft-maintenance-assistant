from dotenv import load_dotenv
load_dotenv()  # load environment variables from .env

import os
import pathlib

# Root of the project (one level up from this file)
ROOT = pathlib.Path(__file__).parent.parent

# Paths
DATASET_DIR = ROOT / "1 Dataset"
INDEX_DIR   = ROOT / "app" / "data" / "index"
MEMORY_DIR  = ROOT / "app" / "data" / "memory"
WEB_DIR     = ROOT / "web"

# API keys and model (override via .env if desired)
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_MODEL     = os.getenv("GROQ_MODEL", "compound-beta")

# Embeddings and PDF backend
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
PDF_BACKEND = os.getenv("PDF_BACKEND", "pypdf")

# App metadata
APP_NAME = "Aircraft Maintenance Assistant"

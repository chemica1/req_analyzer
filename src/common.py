"""
Common utilities and constants shared across the application.
Centralizes configuration, path handling, and embedding initialization.
"""

import os
import sys
import yaml
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Constants
CHROMA_PATH = "chroma_db"
DATA_PATH = "data"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHAT_MODEL = "llama3.2:3b"
DEFAULT_VISION_MODEL = "qwen3-vl:4b"
STATUS_FILE = ".agent_status"


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Relative path to the resource
        
    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def load_config() -> dict:
    """
    Load configuration from config.yaml.
    
    Returns:
        Dictionary with configuration values, using defaults if not found
    """
    # Look for config.yaml in the same directory as the executable
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.getcwd()
    
    config_path = os.path.join(base_path, "config.yaml")
    
    # Default configuration
    config = {
        "chat_model": DEFAULT_CHAT_MODEL,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "vision_model": DEFAULT_VISION_MODEL
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
        except Exception as e:
            print(f"Error loading config.yaml: {e}")
    
    return config


def get_embedding_function(model_name: str = None):
    """
    Initialize and return the embedding function.
    
    Args:
        model_name: Name of the embedding model (uses config default if not provided)
        
    Returns:
        SentenceTransformerEmbeddings instance
    """
    if model_name is None:
        config = load_config()
        model_name = config.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    
    model_path = os.path.join(os.getcwd(), "model_cache")
    if getattr(sys, 'frozen', False):
        model_path = get_resource_path("model_cache")
    
    return SentenceTransformerEmbeddings(
        model_name=model_name,
        cache_folder=model_path
    )


def update_agent_status(status: str):
    """
    Update the agent status file.
    
    Args:
        status: Status message to write
    """
    try:
        with open(STATUS_FILE, "w") as f:
            f.write(status)
    except Exception as e:
        print(f"Error updating status: {e}")

import os
import sys
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

import yaml

# Constants
CHROMA_PATH = "chroma_db"
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_CHAT_MODEL = "llama3.2:3b"

def load_config():
    # Look for config.yaml in the same directory as the executable
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.getcwd()
    
    config_path = os.path.join(base_path, "config.yaml")
    
    config = {
        "chat_model": DEFAULT_CHAT_MODEL,
        "embedding_model": DEFAULT_MODEL_NAME
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

config = load_config()
MODEL_NAME = config["embedding_model"]
CHAT_MODEL = config["chat_model"]

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_embedding_function():
    model_path = os.path.join(os.getcwd(), "model_cache")
    if getattr(sys, 'frozen', False):
        model_path = get_resource_path("model_cache")
    
    return SentenceTransformerEmbeddings(
        model_name=MODEL_NAME,
        cache_folder=model_path
    )

def query_rag(query_text: str, ollama_model: str = CHAT_MODEL):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    # Check if we have any results
    if not results or len(results) == 0:
        # No documents in database - use Ollama directly without RAG
        print("Warning: No documents found in database. Using Ollama without context.")
        model = ChatOllama(model=ollama_model)
        response_text = model.invoke(query_text)
        return response_text, ["No documents indexed yet. Please add PDFs to the data/ folder and click 'Re-index Documents'."], ""
    
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_template = ChatPromptTemplate.from_template(
        """
        Answer the question based only on the following context:

        {context}

        ---

        Answer the question based on the above context: {question}
        """
    )
    
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    model = ChatOllama(model=ollama_model)
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    
    return response_text, sources, context_text

if __name__ == "__main__":
    # Test
    print(query_rag("What is this document about?"))

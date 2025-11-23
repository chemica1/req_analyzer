import os
import sys
import shutil
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Constants
CHROMA_PATH = "chroma_db"
DATA_PATH = "data"
MODEL_NAME = "all-MiniLM-L6-v2"

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_documents(data_folder: str):
    documents = []
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"Created data folder at {data_folder}")
        return []

    for filename in os.listdir(data_folder):
        if filename.endswith(".pdf"):
            file_path = os.path.join(data_folder, filename)
            print(f"Loading {filename}...")
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return documents

def split_text(documents: List):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks: List, persist_directory: str):
    # Clear out the database first to avoid duplicates in this simple implementation
    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)

    # Initialize embedding function
    # We use a local cache folder for the model to ensure it can be bundled
    model_path = os.path.join(os.getcwd(), "model_cache")
    
    # If running in frozen mode (PyInstaller), the model should be in _MEIPASS/model_cache
    if getattr(sys, 'frozen', False):
        model_path = get_resource_path("model_cache")
        print(f"Running in frozen mode. Loading model from {model_path}")
    else:
        print(f"Running in dev mode. Model cache at {model_path}")

    embedding_function = SentenceTransformerEmbeddings(
        model_name=MODEL_NAME,
        cache_folder=model_path
    )

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_function, 
        persist_directory=persist_directory
    )
    print(f"Saved {len(chunks)} chunks to {persist_directory}.")

def ingest(data_folder: str = DATA_PATH):
    documents = load_documents(data_folder)
    if not documents:
        print("No documents found.")
        return
    chunks = split_text(documents)
    save_to_chroma(chunks, CHROMA_PATH)

if __name__ == "__main__":
    ingest()

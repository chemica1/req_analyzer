# Requirement Analyzer - Offline RAG Agentic AI

A local RAG (Retrieval-Augmented Generation) system for analyzing cellular certification requirements from PDF documents. Designed for offline Linux environments.

## Features
- **Offline Operation**: Works without internet after initial setup
- **PDF Analysis**: Extracts and indexes requirement documents
- **Semantic Search**: Uses ChromaDB + SentenceTransformers for retrieval
- **Local LLM**: Integrates with Ollama for generation
- **Web UI**: Streamlit-based chat interface with source citations

## Prerequisites
- **Linux**: x86_64 architecture (or macOS for development)
- **Python**: 3.10+
- **Ollama**: Running locally with `llama3.1` model
  ```bash
  ollama serve
  ollama pull llama3.1
  ```

## Installation (Offline Linux)

### 1. Clone Repository
```bash
git clone https://github.com/chemica1/req_analyzer.git
cd req_analyzer
```

### 2. Build or Run

#### Option A: Build Executable
```bash
chmod +x build_linux.sh
./build_linux.sh
./dist/agent
```

#### Option B: Run with Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=packages -r requirements.txt
streamlit run src/ui.py --server.address=0.0.0.0 --server.headless=true
```

## Configuration
Edit `config.yaml` to change models:
```yaml
ollama_model: "llama3.1"
embedding_model: "all-MiniLM-L6-v2"
```

## Usage
1. Place PDF files in the `data/` folder
2. Open the web UI (default: `http://localhost:8501`)
3. Click "Re-index Documents" in the sidebar
4. Ask questions about the requirements

## Project Structure
```
requirement_agent/
├── src/
│   ├── ingest.py      # PDF processing & embedding
│   ├── rag.py         # Retrieval & generation logic
│   └── ui.py          # Streamlit interface
├── packages/          # Offline Python packages
├── model_cache/       # Embedding model weights
├── data/              # Your PDF documents
├── config.yaml        # Configuration
└── build_linux.sh     # Build script
```

## Troubleshooting
- **Missing torch**: See step 2 above
- **Permission denied**: `chmod +x *.sh`
- **Ollama not found**: Ensure `ollama serve` is running

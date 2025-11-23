#!/bin/bash

# Exit on error
set -e

echo "Setting up build environment..."

# 1. Create and activate virtual environment
if [ ! -d "venv_build" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_build
fi
source venv_build/bin/activate

# 2. Install dependencies (Offline Mode)
echo "Installing dependencies from local packages..."
python3 -m pip install --upgrade pip --no-index --find-links=packages
python3 -m pip install -r requirements.txt --no-index --find-links=packages

# 3. Download the embedding model to a local cache folder so it can be bundled
echo "Downloading embedding model..."
python3 -c "from langchain_community.embeddings import SentenceTransformerEmbeddings; SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2', cache_folder='./model_cache')"

# 4. Run PyInstaller
echo "Building executable..."
pyinstaller agent.spec

echo "Build complete. The executable is in dist/agent"

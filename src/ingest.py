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

def get_indexed_files(persist_directory: str) -> set:
    """Get list of source files already in the vector database."""
    if not os.path.exists(persist_directory):
        return set()
    
    try:
        # Initialize embedding function
        model_path = os.path.join(os.getcwd(), "model_cache")
        if getattr(sys, 'frozen', False):
            model_path = get_resource_path("model_cache")
        
        embedding_function = SentenceTransformerEmbeddings(
            model_name=MODEL_NAME,
            cache_folder=model_path
        )
        
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_function
        )
        
        # Get all documents and extract unique sources
        # Note: This might be slow for very large DBs, but fine for this scale
        result = db.get()
        if result and 'metadatas' in result:
            sources = {m.get('source') for m in result['metadatas'] if m and 'source' in m}
            return sources
        return set()
    except Exception as e:
        print(f"Error checking indexed files: {e}")
        return set()

def load_documents(data_folder: str, progress_callback=None):
    """Load PDFs and analyze them using vision model for richer extraction.
    
    Args:
        data_folder: Path to folder containing PDFs
        progress_callback: Optional callback function(current, total, message) for progress updates
    """
    from pdf2image import convert_from_path
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
    from langchain.schema import Document
    from PIL import Image
    import yaml
    import base64
    import io
    
    # Load config to get vision model
    config_path = os.path.join(os.getcwd(), "config.yaml")
    vision_model = "qwen3-vl:4b"  # default
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'vision_model' in config:
                    vision_model = config['vision_model']
        except Exception as e:
            print(f"Error loading config: {e}")
    
    print(f"Using vision model: {vision_model}")
    
    documents = []
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"Created data folder at {data_folder}")
        return []

    # Get list of PDF files first to calculate total pages
    all_pdf_files = [f for f in os.listdir(data_folder) if f.endswith(".pdf")]
    
    if not all_pdf_files:
        return []

    # Filter out already indexed files
    indexed_files = get_indexed_files(CHROMA_PATH)
    pdf_files = [f for f in all_pdf_files if f not in indexed_files]
    
    if not pdf_files:
        print("All files are already indexed.")
        if progress_callback:
            progress_callback(100, 100, "All files are already indexed.")
        return []
    
    print(f"Found {len(pdf_files)} new files to index out of {len(all_pdf_files)} total.")
    
    # Initialize vision model
    llm = ChatOllama(model=vision_model)
    
    # Calculate total pages for progress tracking
    total_pages = 0
    file_page_counts = {}
    
    if progress_callback:
        progress_callback(0, 100, "Counting PDF pages...")
    
    for filename in pdf_files:
        file_path = os.path.join(data_folder, filename)
        try:
            images = convert_from_path(file_path, dpi=300)
            file_page_counts[filename] = len(images)
            total_pages += len(images)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    current_page = 0
    
    for filename in pdf_files:
        file_path = os.path.join(data_folder, filename)
        print(f"Loading {filename}...")
        
        if progress_callback:
            progress_callback(current_page, total_pages, f"Processing {filename}...")
        
        try:

            # Convert PDF pages to images
            print(f"  Converting PDF to images...")
            images = convert_from_path(file_path, dpi=300)  # Increased to 300 for high quality
            
            # Process each page with vision model
            for page_num, image in enumerate(images, start=1):
                print(f"  Analyzing page {page_num}/{len(images)} with {vision_model}...")
                
                if progress_callback:
                    progress_callback(
                        current_page, 
                        total_pages, 
                        f"Analyzing {filename} - Page {page_num}/{len(images)}"
                    )
                
                # Try with PNG first, then JPEG with compression if it fails
                for attempt in range(2):
                    try:
                        # Convert PIL Image to base64
                        buffered = io.BytesIO()
                        if attempt == 0:
                            # First attempt: PNG (High Quality)
                            image.save(buffered, format="PNG")
                        else:
                            # Second attempt: JPEG with compression (fallback)
                            print(f"    Retrying with compressed JPEG...")
                            image.save(buffered, format="JPEG", quality=85) # Increased quality for fallback too
                        
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Create embedding-optimized prompt with diverse sentence structures
                        prompt = f"""You are a technical document analyst transforming page {page_num} of "{filename}" into embedding-optimized text.

Your goal is to create semantically rich content using DIVERSE sentence structures that preserve all information while maximizing search relevance.

**Sentence Structure Toolkit:**

1. **Definitional (IS-A relationships)**
   - "EMI is an External Machine Interface protocol"
   - "The SMSC is a Short Message Service Centre that manages SMS delivery"
   - Use for: acronyms, technical terms, system components

2. **Functional (Subject-Verb-Object)**
   - "The protocol transmits messages between systems"
   - "Users submit SMS through the EMI interface"
   - Use for: actions, operations, processes

3. **Attributive (HAS-A / WITH properties)**
   - "The system supports multiple protocols including HTTP and SMTP"
   - "Messages contain headers with timestamp and sender information"
   - Use for: features, properties, capabilities

4. **Relational (connects/relates/depends)**
   - "The client connects to the server via TCP port 8000"
   - "Message delivery depends on network availability"
   - Use for: dependencies, connections, relationships

5. **Conditional (IF-THEN logic)**
   - "If authentication fails, the system rejects the connection"
   - "When a message arrives, the SMSC triggers a delivery notification"
   - Use for: rules, logic, behavior

6. **Comparative (differences/similarities)**
   - "Unlike synchronous mode, asynchronous mode allows parallel processing"
   - "Protocol version 4.4a adds support for Unicode compared to version 4.3"
   - Use for: versions, alternatives, options

7. **Quantitative (measurements/values)**
   - "The timeout value is set to 30 seconds"
   - "The system handles up to 1000 messages per second"
   - Use for: specifications, limits, thresholds

8. **Causal (because/therefore/results in)**
   - "The system uses checksums because data integrity is critical"
   - "Network congestion results in delayed message delivery"
   - Use for: reasons, consequences, explanations

**Content Transformation Guidelines:**

**For Tables:**
- Row-by-row: "The first row defines [field] as [value] with [property]"
- Pattern synthesis: "The table maps protocol names to their corresponding port numbers"
- Key insights: "Most protocols use ports in the 8000-9000 range"

**For Diagrams:**
- Components: "The diagram shows three main components: [A], [B], and [C]"
- Flows: "Data flows from [source] through [intermediary] to [destination]"
- Relationships: "[Component A] communicates with [Component B] using [protocol]"

**For Lists:**
- Enumeration: "The system supports five message types: [type1], [type2], [type3], [type4], and [type5]"
- Categorization: "Requirements fall into three categories: functional, performance, and security"
- Prioritization: "Critical parameters include [X], [Y], and [Z], while optional parameters include [A] and [B]"

**For Technical Specifications:**
- Requirements: "The interface must support UTF-8 encoding"
- Constraints: "Message length cannot exceed 160 characters"
- Standards: "The protocol follows the SMPP 3.4 specification"

**Critical Rules:**

✓ Preserve ALL technical details (numbers, names, values)
✓ Define acronyms on first mention: "EMI (External Machine Interface)"
✓ Use varied sentence structures - avoid repetitive patterns
✓ Make implicit information explicit: if a diagram shows arrows, state the direction and meaning
✓ Include context: "In the authentication section, the document specifies..."
✓ Create standalone sentences that don't require visual reference

✗ Don't lose information for the sake of grammar
✗ Don't oversimplify technical content
✗ Don't ignore visual elements like diagrams or tables
✗ Don't use bullet points or fragments

**Example Transformation:**

Visual content: [Diagram showing Client → EMI → SMSC → Mobile Network]

Output: "The system architecture consists of four components connected in sequence. The Client application initiates communication with the EMI interface. EMI serves as the External Machine Interface that connects external systems to the SMSC. The SMSC (Short Message Service Centre) manages message routing and delivery. Finally, the SMSC connects to the Mobile Network for actual SMS transmission. This architecture enables external applications to send SMS messages through a standardized interface."

**Output Format:**
Write a flowing narrative using complete, varied sentences. Each sentence should be information-dense and searchable. Combine related facts into coherent paragraphs. Focus on creating text that will produce high-quality embeddings for semantic search while preserving all technical content.

Ignore decorative elements (logos, borders, watermarks)."""

                        # Analyze with vision model
                        message = HumanMessage(
                            content=[
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": f"data:image/png;base64,{img_base64}"}
                            ]
                        )
                        
                        response = llm.invoke([message])
                        extracted_content = response.content
                        
                        # Create document with extracted content
                        doc = Document(
                            page_content=extracted_content,
                            metadata={
                                "source": filename,
                                "page": page_num,
                                "total_pages": len(images)
                            }
                        )
                        documents.append(doc)
                        print(f"  ✓ Page {page_num} analyzed ({len(extracted_content)} chars)")
                        
                        # Success - break out of retry loop
                        break
                        
                    except Exception as page_error:
                        if attempt == 0:
                            print(f"    Error on attempt {attempt + 1}: {page_error}")
                            print(f"    Will retry with compressed image...")
                            continue
                        else:
                            # Both attempts failed
                            print(f"  ✗ Failed to analyze page {page_num} after {attempt + 1} attempts: {page_error}")
                            # Continue to next page instead of crashing
                            break
                
                current_page += 1
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"Total documents extracted: {len(documents)}")
    
    if progress_callback:
        progress_callback(total_pages, total_pages, "Analysis complete!")
    
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
    # Incremental update: Do NOT clear out the database
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)

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

def ingest(data_folder: str = DATA_PATH, progress_callback=None):
    documents = load_documents(data_folder, progress_callback=progress_callback)
    if not documents:
        print("No documents found.")
        return
    
    if progress_callback:
        progress_callback(0, 100, "Splitting documents into chunks...")
    
    chunks = split_text(documents)
    
    if progress_callback:
        progress_callback(0, 100, "Creating embeddings and saving to database...")
    
    save_to_chroma(chunks, CHROMA_PATH)

if __name__ == "__main__":
    ingest()

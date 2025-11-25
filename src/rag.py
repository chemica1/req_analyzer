from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from common import CHROMA_PATH, load_config, get_embedding_function

# Load configuration
config = load_config()
CHAT_MODEL = config.get("chat_model", "llama3.2:3b")



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

def get_all_documents():
    """Retrieve all documents from the vector database for inspection."""
    try:
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        
        results = db.get()
        
        docs = []
        if results and 'documents' in results:
            for i, content in enumerate(results['documents']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                docs.append({
                    "content": content,
                    "source": metadata.get("source", "Unknown"),
                    "page": metadata.get("page", "N/A"),
                    "total_pages": metadata.get("total_pages", "N/A")
                })
        return docs
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []

if __name__ == "__main__":
    # Test
    print(query_rag("What is this document about?"))

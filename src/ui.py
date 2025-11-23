import streamlit as st
import os
import sys
from ingest import ingest
from rag import query_rag

st.set_page_config(page_title="Agentic AI Requirement Analyst", layout="wide")

st.title("Agentic AI: Cellular Requirement Analyst")
st.markdown("Ask questions about cellular certification requirements based on the provided PDFs.")

# Sidebar for configuration
with st.sidebar:
    st.header("📁 Document Management")
    data_folder = st.text_input("PDF Data Folder", value="data")
    
    # Create data folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    
    # PDF Upload Section
    st.subheader("Upload PDFs")
    uploaded_files = st.file_uploader(
        "Choose PDF files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload one or more PDF files to analyze"
    )
    
    auto_reindex = st.checkbox("Auto re-index after upload", value=True)
    
    if uploaded_files:
        if st.button("💾 Save Uploaded Files"):
            with st.spinner("Saving files..."):
                saved_files = []
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(data_folder, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_files.append(uploaded_file.name)
                
                st.success(f"✅ Saved {len(saved_files)} file(s): {', '.join(saved_files)}")
                
                # Auto re-index if enabled
                if auto_reindex:
                    st.markdown("### 📊 Indexing Progress")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total, message):
                        if total > 0:
                            progress = current / total
                            progress_bar.progress(progress)
                            status_text.text(f"{message} ({current}/{total} pages - {int(progress * 100)}%)")
                        else:
                            status_text.text(message)
                    
                    try:
                        ingest(data_folder, progress_callback=update_progress)
                        progress_bar.progress(1.0)
                        status_text.text("✅ Re-indexing complete!")
                        st.success("✅ Re-indexing complete!")
                    except Exception as e:
                        st.error(f"Error during re-indexing: {e}")
                        import traceback
                        st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # List existing PDFs
    st.subheader("📄 Existing PDFs")
    pdf_files = [f for f in os.listdir(data_folder) if f.endswith('.pdf')] if os.path.exists(data_folder) else []
    
    if pdf_files:
        st.write(f"**{len(pdf_files)} PDF(s) found:**")
        for pdf_file in pdf_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"📄 {pdf_file}")
            with col2:
                if st.button("🗑️", key=f"delete_{pdf_file}", help=f"Delete {pdf_file}"):
                    try:
                        os.remove(os.path.join(data_folder, pdf_file))
                        st.success(f"Deleted {pdf_file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {e}")
    else:
        st.info("No PDF files found. Upload some PDFs to get started!")
    
    st.markdown("---")
    
    
    # Manual Re-index Button
    if st.button("🔄 Re-index All Documents"):
        st.markdown("### 📊 Indexing Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, message):
            if total > 0:
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"{message} ({current}/{total} pages - {int(progress * 100)}%)")
            else:
                status_text.text(message)
        
        try:
            ingest(data_folder, progress_callback=update_progress)
            progress_bar.progress(1.0)
            status_text.text("✅ Ingestion complete!")
            st.success("✅ Ingestion complete!")
        except Exception as e:
            st.error(f"Error during ingestion: {e}")
            import traceback
            st.code(traceback.format_exc())

    st.markdown("---")
    st.markdown("**Note**: Ensure Ollama is running locally.")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message["sources"]:
                    st.write(f"- {source}")

if prompt := st.chat_input("Ask a question about requirements (e.g., 'Does KT require SMS over IMS?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response_msg, sources, context = query_rag(prompt)
                # response_msg is a AIMessage object from LangChain, we need .content
                response_content = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
                
                st.markdown(response_content)
                with st.expander("View Sources"):
                    unique_sources = list(set(sources))
                    for source in unique_sources:
                        st.write(f"- {source}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_content,
                    "sources": unique_sources
                })
            except Exception as e:
                st.error(f"An error occurred: {e}")

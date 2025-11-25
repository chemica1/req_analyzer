import streamlit as st
import os
import sys
import pandas as pd
from ingest import ingest
from rag import query_rag, get_all_documents

st.set_page_config(page_title="Agentic AI Requirement Analyst", layout="wide")

st.title("Agentic AI: Cellular Requirement Analyst")
st.markdown("Ask questions about cellular certification requirements based on the provided PDFs.")

# Sidebar for configuration
# Sidebar for configuration
with st.sidebar:
    st.header("🤖 Agent Status")
    
    # Background Agent Status
    status_placeholder = st.empty()
    status_file = ".agent_status"
    
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            status = f.read().strip()
        status_placeholder.info(f"**Status:** {status}")
    else:
        status_placeholder.warning("Status: Unknown (Agent not started)")
        
    # Sync Button (Triggers incremental ingest)
    if st.button("� Sync Documents Now", use_container_width=True):
        with st.spinner("Syncing documents..."):
            try:
                # Run incremental ingest
                def update_progress(current, total, message):
                    pass 
                
                ingest("data", progress_callback=update_progress)
                st.success("Sync complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Error syncing: {e}")

    st.divider()
    
    st.header("� Document Management")
    
    # PDF Upload Section
    uploaded_files = st.file_uploader(
        "Upload New PDFs", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload PDF files to add them to the knowledge base"
    )
    
    if uploaded_files:
        if st.button("💾 Save & Process", use_container_width=True):
            with st.spinner("Saving files..."):
                saved_files = []
                if not os.path.exists("data"):
                    os.makedirs("data")
                    
                for uploaded_file in uploaded_files:
                    file_path = os.path.join("data", uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_files.append(uploaded_file.name)
                
                st.success(f"Saved {len(saved_files)} files.")
                
                # Trigger ingest immediately after save
                with st.spinner("Indexing new files..."):
                     ingest("data", progress_callback=None)
                
                st.rerun()
    
    # List existing PDFs
    st.subheader("Library")
    pdf_files = [f for f in os.listdir("data") if f.endswith('.pdf')] if os.path.exists("data") else []
    
    if pdf_files:
        st.caption(f"{len(pdf_files)} document(s) available")
        for pdf_file in pdf_files:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"📄 {pdf_file}")
            with col2:
                if st.button("🗑️", key=f"delete_{pdf_file}", help=f"Delete {pdf_file}"):
                    try:
                        os.remove(os.path.join("data", pdf_file))
                        st.success("Deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("Library is empty. Upload PDFs to start.")
    
    st.divider()
    st.caption("Powered by Ollama (Llama 3.2 & Qwen 2.5 VL)")

# Main Content Tabs
tab1, tab2 = st.tabs(["💬 Chat", "🔍 Database Explorer"])

with tab1:
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

with tab2:
    st.header("Database Explorer")
    st.caption("View all embedded chunks stored in ChromaDB")
    
    # Fetch all documents
    with st.spinner("Loading database contents..."):
        all_docs = get_all_documents()
    
    if not all_docs:
        st.warning("No documents found in the database. Upload and sync PDFs to get started.")
    else:
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chunks", len(all_docs))
        with col2:
            unique_sources = len(set(doc["source"] for doc in all_docs))
            st.metric("Unique Documents", unique_sources)
        with col3:
            total_chars = sum(len(doc["content"]) for doc in all_docs)
            st.metric("Total Characters", f"{total_chars:,}")
        
        st.divider()
        
        # Filter by source
        all_sources = sorted(set(doc["source"] for doc in all_docs))
        selected_source = st.selectbox(
            "Filter by document:",
            ["All"] + all_sources,
            index=0
        )
        
        # Filter documents
        if selected_source != "All":
            filtered_docs = [doc for doc in all_docs if doc["source"] == selected_source]
        else:
            filtered_docs = all_docs
        
        st.caption(f"Showing {len(filtered_docs)} chunk(s)")
        
        # Display as table
        df = pd.DataFrame(filtered_docs)
        df['preview'] = df['content'].str[:100] + '...'
        display_df = df[['source', 'page', 'preview']].copy()
        display_df.columns = ['Source File', 'Page', 'Content Preview']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Detail view
        st.subheader("Chunk Details")
        chunk_index = st.number_input(
            "Select chunk index to view full content:",
            min_value=0,
            max_value=len(filtered_docs) - 1 if filtered_docs else 0,
            value=0,
            step=1
        )
        
        if filtered_docs:
            selected_chunk = filtered_docs[chunk_index]
            with st.expander(f"📄 {selected_chunk['source']} - Page {selected_chunk['page']}", expanded=True):
                st.text_area(
                    "Full Content:",
                    selected_chunk['content'],
                    height=300,
                    disabled=True
                )

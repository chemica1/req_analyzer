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
    st.header("Configuration")
    data_folder = st.text_input("PDF Data Folder", value="data")
    
    if st.button("Re-index Documents"):
        with st.spinner("Ingesting documents... This may take a while."):
            try:
                ingest(data_folder)
                st.success("Ingestion complete!")
            except Exception as e:
                st.error(f"Error during ingestion: {e}")

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

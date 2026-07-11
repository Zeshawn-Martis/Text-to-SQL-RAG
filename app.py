import streamlit as st
import pandas as pd
from engine import run_agentic_pipeline

st.set_page_config(page_title="RAG Text-to-SQL Copilot", page_icon="🧠", layout="centered")

st.title("🧠 Agentic Text to SQL")
st.caption("Text to SQL using Gemini & ChromaDB.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hi! Ask me anything about our movie database.", "metadata": None}
    ]

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Display the Cookbook architectural details inside an expander
        if msg.get("metadata"):
            meta = msg["metadata"]
            
            with st.expander("🔍 Inside the Agent's Brain (Cookbook Steps)"):
                # 1. RAG Context
                st.markdown("**1. ChromaDB Retrieved Few-Shot Examples (RAG):**")
                st.info(meta["retrieved_examples"] if meta["retrieved_examples"] else "No closely related examples found.")
                
                # 2. Chain of Thought
                st.markdown("**2. LLM Chain of Thought (`<thinking>` tags):**")
                st.success(meta["thinking"])
                
                # 3. Generated SQL
                st.markdown("**3. Generated SQL (`<sql>` tags):**")
                st.code(meta["sql"], language="sql")
                
                # 4. Self-Correction flag
                if meta["was_corrected"]:
                    st.warning("⚠️ The agent detected a SQL error during execution and successfully self-corrected the query!")
                
                # 5. Raw Result
                st.markdown("**4. Raw Database Execution Result:**")
                if isinstance(meta["raw_data"], pd.DataFrame):
                    st.dataframe(meta["raw_data"], hide_index=True)
                else:
                    st.error(meta["raw_data"])

if user_input := st.chat_input("e.g., Which sci-fi movie grossed the most at the box office?"):
    
    # Render user message
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Process through pipeline
    with st.chat_message("assistant"):
        with st.spinner("Retrieving schema, thinking step-by-step, and executing..."):
            
            # Run the Cookbook architecture pipeline
            try:
                result = run_agentic_pipeline(user_input)
                
                # Display the final natural language answer
                st.write(result["answer"])
                
                with st.expander("🔍 Inside the Agent's Brain (Cookbook Steps)"):
                    st.markdown("**1. ChromaDB Retrieved Few-Shot Examples (RAG):**")
                    st.info(result["retrieved_examples"] if result["retrieved_examples"] else "No closely related examples found.")
                    
                    st.markdown("**2. LLM Chain of Thought (`<thinking>` tags):**")
                    st.success(result["thinking"])
                    
                    st.markdown("**3. Generated SQL (`<sql>` tags):**")
                    st.code(result["sql"], language="sql")
                    
                    if result["was_corrected"]:
                        st.warning("⚠️ The agent detected a SQL error during execution and successfully self-corrected the query!")
                    
                    st.markdown("**4. Raw Database Execution Result:**")
                    if isinstance(result["raw_data"], pd.DataFrame):
                        st.dataframe(result["raw_data"], hide_index=True)
                    else:
                        st.error(result["raw_data"])

                # Save state
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "metadata": result
                })
            except Exception as e:
                st.error(f"Pipeline crashed. Please ensure your GOOGLE_API_KEY is set. Error details: {e}")
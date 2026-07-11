# 🧠 Agentic Text-to-SQL Copilot

An AI-powered application that converts natural language questions into SQL queries and executes them on a database.

Built using **Gemini, LangChain, ChromaDB, Sentence Transformers, SQLite, and Streamlit**.

## Features

- Ask database questions using plain English
- Automatically generates and executes SQL queries
- Uses RAG with ChromaDB to retrieve previous SQL examples
- Self-corrects SQL errors using Gemini
- Displays generated SQL and query results

## Tech Stack

- **LLM:** Google Gemini
- **Framework:** LangChain
- **Vector Database:** ChromaDB
- **Embeddings:** Sentence Transformers
- **Database:** SQLite
- **Frontend:** Streamlit

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Zeshawn-Martis/Text-to-SQL-RAG.git
cd Text-to-SQL-RAG

import os
import sqlite3
import uuid
import pandas as pd
import chromadb
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ENVIRONMENT
load_dotenv()
DB_PATH = "movies.db"

# SQLITE DATABASE
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS directors(id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE IF NOT EXISTS movies(
            id INTEGER PRIMARY KEY, 
            title TEXT, 
            genre TEXT, 
            rating REAL, 
            director_id INTEGER, 
            FOREIGN KEY(director_id) REFERENCES directors(id)
        );
    """)
    if cursor.execute("SELECT COUNT(*) FROM directors").fetchone()[0] == 0:
        cursor.executemany("INSERT INTO directors VALUES (?,?)", [
            (1, "Christopher Nolan"), (2, "Denis Villeneuve"), (3, "Greta Gerwig")
        ])
        cursor.executemany("INSERT INTO movies (title,genre,rating,director_id) VALUES (?,?,?,?)", [
            ("Inception", "Sci-Fi", 8.8, 1), ("Interstellar", "Sci-Fi", 8.6, 1),
            ("Dune", "Sci-Fi", 8.0, 2), ("Arrival", "Sci-Fi", 7.9, 2),
            ("Barbie", "Comedy", 7.0, 3), ("Little Women", "Drama", 7.8, 3)
        ])
    conn.commit()
    conn.close()

def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    try:
        result = pd.read_sql_query(sql, conn)
        conn.close()
        return result
    except Exception as e:
        conn.close()
        return f"Database Error: {e}"

# CHROMADB + EMBEDDINGS
embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_rag_cache")
memory_db = chroma_client.get_or_create_collection(name="sql_memory", embedding_function=embedding_function)

# GEMINI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, max_retries=0)

# PROMPTS
sql_prompt = ChatPromptTemplate.from_template("""
You are a SQL expert. Database schema: directors(id, name), movies(id, title, genre, rating, director_id).
Rules: 1. Generate ONLY SQLite SQL. 2. Put SQL inside <sql></sql>. 3. No markdown. 4. Use examples if relevant.
Question: {question}
Previous examples: {examples}
""")

fix_prompt = ChatPromptTemplate.from_template("""
You are a SQL debugging expert. The SQL failed with: {error}
Question: {question}
Return ONLY corrected SQLite SQL inside <sql></sql>.
""")

answer_prompt = ChatPromptTemplate.from_template("Explain the result to the user. Question: {question}\nResult: {data}")

# CHAINS
sql_chain = sql_prompt | llm | StrOutputParser()
fix_chain = fix_prompt | llm | StrOutputParser()
answer_chain = answer_prompt | llm | StrOutputParser()

# HELPERS
def extract_sql(text):
    if "<sql>" in text and "</sql>" in text:
        return text.split("<sql>")[1].split("</sql>")[0].strip()
    return text.replace("```sql", "").replace("```", "").strip()

def extract_thinking(text):
    return text.split("<thinking>")[1].split("</thinking>")[0] if "<thinking>" in text else "No reasoning"

# RAG AGENT
def run_agentic_pipeline(user_question):
    examples, final_sql, thinking, corrected = "", "", "", False
    
    # Retrieval
    if memory_db.count() > 0:
        retrieved = memory_db.query(query_texts=[user_question], n_results=3)
        if retrieved["documents"][0]:
            examples = "\n\n".join(retrieved["documents"][0])

    # Generation & Execution
    response = sql_chain.invoke({"question": user_question, "examples": examples})
    final_sql, thinking = extract_sql(response), extract_thinking(response)
    db_result = run_query(final_sql)

    # Self-Healing
    if isinstance(db_result, str) and "Database Error" in db_result:
        final_sql = extract_sql(fix_chain.invoke({"error": db_result, "question": user_question}))
        db_result = run_query(final_sql)
        corrected = True

    # Memory Update
    if not isinstance(db_result, str):
        memory_db.add(documents=[f"Question: {user_question}\nSQL: {final_sql}"], 
                      metadatas=[{"sql": final_sql}], ids=[str(uuid.uuid4())])

    return {
        "answer": answer_chain.invoke({"question": user_question, "data": db_result.to_string()}),
        "sql": final_sql,
        "thinking": thinking,
        "retrieved_examples": examples,
        "raw_data": db_result,
        "was_corrected": corrected
    }

setup_database()
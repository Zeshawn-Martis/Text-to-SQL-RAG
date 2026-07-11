import sqlite3
import uuid
import pandas as pd
import chromadb
import streamlit as st

from dotenv import load_dotenv

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import (
    ChatPromptTemplate
)

from langchain_core.output_parsers import (
    StrOutputParser
)



# ENVIRONMENT

load_dotenv()

DB_PATH = "database/movies.db"



# DATABASE QUERY

def run_query(sql):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        result = pd.read_sql_query(
            sql,
            conn
        )

        conn.close()

        return result


    except Exception as e:

        conn.close()

        return f"Database Error: {e}"



# FETCH DATABASE SCHEMA

def get_database_schema():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type='table'
        """
    )


    tables = cursor.fetchall()

    conn.close()


    return "\n\n".join(
        x[0]
        for x in tables
        if x[0]
    )



# CHROMADB

@st.cache_resource
def load_embedding():

    return SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )



@st.cache_resource
def load_chroma():

    client = chromadb.PersistentClient(
        path="./chroma_rag_cache"
    )


    return client.get_or_create_collection(
        name="sql_memory",
        embedding_function=load_embedding()
    )



def get_memory_db():

    return load_chroma()



# GEMINI

@st.cache_resource
def load_llm():

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        max_retries=0
    )



llm = load_llm()



# SAFE GEMINI CALL

def safe_invoke(chain, inputs):

    try:

        return chain.invoke(inputs)


    except Exception as e:

        error = str(e).lower()


        if any(
            x in error
            for x in [
                "429",
                "quota",
                "resourceexhausted",
                "rate limit"
            ]
        ):

            raise RuntimeError(
                "Gemini quota exceeded."
            )


        raise RuntimeError(
            f"Gemini error: {e}"
        )



# SQL GENERATION PROMPT

sql_prompt = ChatGoogleGenerativeAI


sql_prompt = ChatPromptTemplate.from_template(
"""

You are a SQL expert.

Database schema:

{schema}


Rules:

1. Generate only SQLite SQL.
2. Put SQL inside <sql></sql>.
3. No markdown.
4. Only use existing columns.
5. Use joins when required.


Question:

{question}


Previous examples:

{examples}

"""
)



# SQL FIX PROMPT

fix_prompt = ChatPromptTemplate.from_template(
"""

You are a SQL debugging expert.

Database schema:

{schema}


SQL error:

{error}


Question:

{question}


Return only corrected SQLite SQL.

Use:

<sql>
query
</sql>

"""
)



sql_chain = (
    sql_prompt
    | llm
    | StrOutputParser()
)



fix_chain = (
    fix_prompt
    | llm
    | StrOutputParser()
)



# EXTRACT SQL

def extract_sql(text):

    if "<sql>" in text:

        return (
            text
            .split("<sql>")[1]
            .split("</sql>")[0]
            .strip()
        )


    return (
        text
        .replace("```sql","")
        .replace("```","")
        .strip()
    )



# MAIN PIPELINE

def run_agentic_pipeline(question):


    memory_db = get_memory_db()


    examples = ""

    corrected = False



    # RETRIEVE OLD SQL EXAMPLES

    if memory_db.count() > 0:

        result = memory_db.query(
            query_texts=[question],
            n_results=1
        )


        if result["documents"][0]:

            examples = (
                result["documents"][0][0]
            )



    schema = get_database_schema()



    # GENERATE SQL

    response = safe_invoke(
        sql_chain,
        {
            "question": question,
            "schema": schema,
            "examples": examples
        }
    )


    sql = extract_sql(response)



    # EXECUTE SQL

    db_result = run_query(sql)



    # SELF HEALING

    if (
        isinstance(db_result,str)
        and
        "Database Error" in db_result
    ):


        corrected = True


        fixed = safe_invoke(
            fix_chain,
            {
                "error": db_result,
                "question": question,
                "schema": schema
            }
        )


        sql = extract_sql(
            fixed
        )


        db_result = run_query(sql)



    # SAVE MEMORY

    if not isinstance(
        db_result,
        str
    ):


        memory_db.add(

            documents=[

                f"""
Question:
{question}

SQL:
{sql}
"""
            ],

            metadatas=[

                {
                    "sql": sql
                }

            ],

            ids=[

                str(uuid.uuid4())

            ]
        )



    # FINAL ANSWER

    if isinstance(
        db_result,
        str
    ):

        answer = db_result


    else:

        answer = db_result.to_markdown(
            index=False
        )


    return {

        "answer": answer,

        "sql": sql,

        "retrieved_examples": examples,

        "raw_data": db_result,

        "was_corrected": corrected

    }
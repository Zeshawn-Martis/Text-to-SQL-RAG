import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Agentic Text-to-SQL",
    page_icon="🧠"
)


from engine import run_agentic_pipeline



st.title(
    "🧠 Agentic Text-to-SQL"
)


st.caption(
    "Ask questions about your database using natural language."
)



if "chat_history" not in st.session_state:

    st.session_state.chat_history = [

        {
            "role":"assistant",
            "content":
            "Hi! Ask me anything about the movie database.",
            "metadata":None
        }

    ]



def display_metadata(data):

    with st.expander(
        "🔍 SQL Details"
    ):

        st.code(
            data["sql"],
            language="sql"
        )


        if data["was_corrected"]:

            st.warning(
                "SQL was automatically corrected."
            )


        if isinstance(
            data["raw_data"],
            pd.DataFrame
        ):

            st.dataframe(
                data["raw_data"],
                hide_index=True
            )



for msg in st.session_state.chat_history:

    with st.chat_message(
        msg["role"]
    ):

        st.write(
            msg["content"]
        )


        if msg["metadata"]:

            display_metadata(
                msg["metadata"]
            )




if question := st.chat_input(
    "Ask something..."
):


    st.session_state.chat_history.append(
        {
            "role":"user",
            "content":question,
            "metadata":None
        }
    )


    with st.chat_message("user"):

        st.write(question)



    with st.chat_message("assistant"):


        try:

            result = run_agentic_pipeline(
                question
            )


            st.write(
                result["answer"]
            )


            display_metadata(
                result
            )


            st.session_state.chat_history.append(
                {
                    "role":"assistant",
                    "content":result["answer"],
                    "metadata":result
                }
            )


        except Exception as e:

            st.error(
                str(e)
            )
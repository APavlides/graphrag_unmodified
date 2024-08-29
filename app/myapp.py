import streamlit as st

from global_query import execute_global_query
from local_query import execute_local_query
import asyncio
import os
from datetime import datetime
from fpdf import FPDF


if "run_once" not in st.session_state:
    st.session_state["run_once"] = True

# Specify the directory containing the text files
TEXT_FILES_DIR = "./input/"

# Get a list of all .txt files in the directory
txt_files = [f for f in os.listdir(TEXT_FILES_DIR) if f.endswith(".txt")]


# Cache the main function's response using the st.cache_data decorator
@st.cache_data(show_spinner=False)
def get_cached_global_response(question_str):
    return asyncio.run(execute_global_query(question=question_str, mock=False))


@st.cache_data(show_spinner=False)
def get_cached_local_response(question_str):
    return asyncio.run(execute_local_query(question=question_str, mock=False))


# Tab selector
tab = st.sidebar.radio("Select a tab", ["Search Documents", "View Documents"])


if tab == "Search Documents":

    # Adding a title to the main area
    st.title("Q&A Patient History")

    help_text = """Global Search vs. Local Search in GraphRAG \n
Local Search focuses on a specific subgraph or a local neighborhood of nodes within the knowledge graph. It is well-suited for answering questions that require an understanding of specific entities mentioned in the input documents (e.g., “When was John Doe born?”).

Global Search is used when the query requires a broad understanding and connections from various parts of the graph. It’s useful for queries that are not highly specific and benefit from a wider context. Queries such as “Explain what treatments have been tried and has anything worked?”\n

Note: You will find that you get a Local and Global response for a given question, but for a question like “Explain what treatments have been tried and has anything worked? you will get a breader answer if using Global search than Local search. Similarly, for a specific question about date of birth you may or may not get an answer with Global search, because a Local search is more appropriate. 
"""

    # Graphrag search type
    search_type = st.sidebar.radio(
        "Type of Search", ["Global", "Local"], help=help_text
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state["run_once"] == True:
        st.session_state["run_once"] = False

        # Init questions

        user_q_list = [
            {
                "question": "What is the patient's name, age and date of birth, if known?",
                "type": "local",
            },
            {"question": "Who does the patient live with if known", "type": "local"},
            {
                "question": "What is the patient's early development history if known i.e. traumas, significant events, what school they went to.",
                "type": "global",
            },
            {"question": "Why is the patient coming to the clinic?", "type": "global"},
            {
                "question": "Have social services been involved or has the patient had other early help",
                "type": "global",
            },
            {"question": "What is the patient's condition history.", "type": "global"},
            {
                "question": "What drugs has the patient been prescribed previously if known",
                "type": "local",
            },
            {"question": "What does the patient want?", "type": "global"},
        ]

        for q in user_q_list:

            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(q["question"])
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": q["question"]})

            # response = get_cached_response(prompt)
            # output = "This is just a test"

            try:
                with st.spinner("Model is working on it..."):
                    if q["type"] == "global":
                        result = get_cached_global_response(question_str=q["question"])
                    elif q["type"] == "local":
                        result = get_cached_local_response(question_str=q["question"])
                    output = result.response
                    # st.subheader(f":blue[{i}]")
                    # st.write(reponse.response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error(
                    "Oops, the GPT response resulted in an error :( Please try again with a different question."
                )
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(output)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": output})

    if additional_q := st.chat_input("Ask additional questions..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(additional_q)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": additional_q})

        # response = get_cached_response(prompt)
        # output = "This is just a test"

        try:
            with st.spinner("Model is working on it..."):
                if search_type == "Global":
                    result = get_cached_global_response(question_str=additional_q)
                elif search_type == "Local":
                    result = get_cached_local_response(question_str=additional_q)

                output = result.response
                # st.subheader(f":blue[{i}]")
                # st.write(reponse.response)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error(
                "Oops, the GPT response resulted in an error :( Please try again with a different question."
            )

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(output)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": output})  #

    # # Function to format the chat history into a string
    # def format_messages_for_text(messages):
    #     formatted = []
    #     for msg in messages:
    #         role = "User" if msg["role"] == "user" else "Assistant"
    #         content = msg["content"]
    #         formatted.append(f"{role}: {content}")
    #     return "\n".join(formatted)

    # # Format messages for the text file
    # if st.session_state.messages:
    #     messages_str = format_messages_for_text(st.session_state.messages)

    #     # Convert the string to bytes
    #     messages_bytes = messages_str.encode("utf-8")

    #     # Create a download button for the text file
    #     st.sidebar.download_button(
    #         label="Download Chat History as Text File",
    #         data=messages_bytes,
    #         file_name="chat_history.txt",
    #         mime="text/plain",
    #     )
    # else:
    #     st.write("No messages stored yet.")

    # Function to format the chat history into a PDF
    def format_messages_for_pdf(messages):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Set font for the header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Summary Report", ln=True, align="C")

        # Add date
        date_str = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, date_str, ln=True, align="C")
        pdf.ln(10)  # Add some space after the date

        # Process each message and add it to the PDF
        for i in range(0, len(messages), 2):
            user_msg = messages[i]
            if user_msg["role"] == "user":
                pdf.set_font("Arial", "B", 14)
                question = f"Question {i // 2 + 1}:"
                pdf.cell(0, 10, question, ln=True)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, user_msg["content"])
                pdf.ln(5)

            # Ensure there's a corresponding assistant response
            if i + 1 < len(messages):
                assistant_msg = messages[i + 1]
                if assistant_msg["role"] == "assistant":
                    pdf.set_font("Arial", "B", 14)
                    response_header = "Summary:"
                    pdf.cell(0, 10, response_header, ln=True)
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, assistant_msg["content"])
                    pdf.ln(10)

        return pdf.output(dest="S").encode("latin1")

    # Format messages for the PDF file
    if st.session_state.messages:
        messages_bytes = format_messages_for_pdf(st.session_state.messages)

        # Create a download button for the PDF file
        st.sidebar.download_button(
            label="Download Summary Report",
            data=messages_bytes,
            file_name="chat_history.pdf",
            mime="application/pdf",
        )
    else:
        st.write("No messages stored yet.")

    # import streamlit as st
    # from datetime import datetime

    # # Function to format the chat history into a markdown string
    # def format_messages_for_markdown(messages):
    #     formatted = []
    #     # Add a header and date to the markdown
    #     header = "# Chat History Report"
    #     date_str = f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    #     formatted.append(header)
    #     formatted.append(date_str)
    #     formatted.append("\n")

    #     # Process each message and format as markdown sections
    #     for i in range(0, len(messages), 2):
    #         user_msg = messages[i]
    #         if user_msg["role"] == "user":
    #             question = f"## Question {i // 2 + 1}\n{user_msg['content']}"
    #             formatted.append(question)

    #         # Ensure there's a corresponding assistant response
    #         if i + 1 < len(messages):
    #             assistant_msg = messages[i + 1]
    #             if assistant_msg["role"] == "assistant":
    #                 response = f"### Response\n{assistant_msg['content']}"
    #                 formatted.append(response)

    #         formatted.append("\n")

    #     return "\n".join(formatted)

    # # Format messages for the markdown file
    # if st.session_state.messages:
    #     messages_str = format_messages_for_markdown(st.session_state.messages)

    #     # Convert the string to bytes
    #     messages_bytes = messages_str.encode("utf-8")

    #     # Create a download button for the markdown file
    #     st.sidebar.download_button(
    #         label="Download Chat History as Markdown File",
    #         data=messages_bytes,
    #         file_name="chat_history.md",
    #         mime="text/markdown",
    #     )
    # else:
    #     st.write("No messages stored yet.")


elif tab == "View Documents":
    st.title("Document Viewer")

    if txt_files:
        # Dropdown menu to select a file
        selected_file = st.selectbox("Select a text file", txt_files)

        # Load and display the selected file's content
        if selected_file:
            file_path = os.path.join(TEXT_FILES_DIR, selected_file)
            with open(file_path, "r") as file:
                file_content = file.read()

            st.subheader(f"Contents of {selected_file}:")
            st.markdown(file_content)
    else:
        st.write("No text files found in the directory.")

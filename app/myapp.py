import streamlit as st

from global_query import execute_global_query
from local_query import execute_local_query
import asyncio
import os


if "run_once" not in st.session_state:
    st.session_state["run_once"] = True

# Specify the directory containing the text files
TEXT_FILES_DIR = "./input/"

# Get a list of all .txt files in the directory
txt_files = [f for f in os.listdir(TEXT_FILES_DIR) if f.endswith(".txt")]


# Cache the main function's response using the st.cache_data decorator
@st.cache_data(show_spinner=False)
def get_cached_global_response(question):
    return asyncio.run(execute_global_query(question=question, mock=False))


@st.cache_data(show_spinner=False)
def get_cached_local_response(question):
    return asyncio.run(execute_local_query(question=question, mock=False))


# Tab selector
tab = st.sidebar.radio("Select a tab", ["Search Documents", "View Documents"])


if tab == "Search Documents":

    # Adding a title to the main area
    st.title("Q&A Patient History")

    # Graphrag search type
    search_type = st.sidebar.radio("Type of Search", ["Global", "Local"])

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

        # user_q_list = ["What drugs has the patient been prescribed previously if known",
        #                "What is the age of the patient if known",
        #                "Who does the patient live with if known",
        #                "What is their early development history if known i.e. traumas, significant events, what school they went to.",
        #                "Why is the patient coming to the clinic?",
        #                "Have social services been involved or has the patient had other early help",
        #                "What is the patient's condition history.",
        #                "What does the patient want?"]
        user_q_list = [
            (
                "What drugs has the patient been prescribed previously if known",
                "Global",
            ),
            ("What treatment has the patient received previously.", "Global"),
            (
                "What is the age, or data of birth (DOB), of the patient if known",
                "Local",
            ),
        ]

        for q in user_q_list:

            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(q[0])
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": q[0]})

            # response = get_cached_response(prompt)
            # output = "This is just a test"

            try:
                with st.spinner("Model is working on it..."):
                    if q[1] == "Global":
                        result = get_cached_global_response(question=q[0])
                    elif q[1] == "Local":
                        result = get_cached_local_response(question=q[0])
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

    if prompt := st.chat_input("Ask additional questions..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # response = get_cached_response(prompt)
        # output = "This is just a test"

        try:
            with st.spinner("Model is working on it..."):
                if search_type == "Global":
                    result = get_cached_global_response(question=q)
                elif search_type == "Local":
                    result = get_cached_local_response(question=q)

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

    # Function to format the chat history into a string
    def format_messages_for_text(messages):
        formatted = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    # Format messages for the text file
    if st.session_state.messages:
        messages_str = format_messages_for_text(st.session_state.messages)

        # Convert the string to bytes
        messages_bytes = messages_str.encode("utf-8")

        # Create a download button for the text file
        st.sidebar.download_button(
            label="Download Chat History as Text File",
            data=messages_bytes,
            file_name="chat_history.txt",
            mime="text/plain",
        )
    else:
        st.write("No messages stored yet.")

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

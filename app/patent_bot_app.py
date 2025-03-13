import streamlit as st
import requests
import time

st.title("🤖 Patent Bot 📑")
st.markdown("#### Hi Ariel, I'm here to assist you with responding to the Office Action. \
    Please upload the patent application and the office action, and then click the button to get started.")
st.markdown("")

patent_application_file = st.file_uploader("Upload the patent application")
office_action_file = st.file_uploader("Upload the office action")

# Base url and all the endpoints
base_url = "https://response-to-oa-image-2dkcwif5ra-ew.a.run.app"

text_extraction_url = base_url + "/text_extraction"
fetch_references_url = base_url + "/fetching_references"
retrieve_knowledge_base_url = base_url + "/retrieve_knowledge_base"
planning_strategy_url = base_url + "/planning_strategy"
execute_strategy_url = base_url + "/execute_strategy"
generate_draft_url = base_url + "/generate_draft"


# Functions for each step of the process
def load_files_and_extract_info():

    if patent_application_file and office_action_file:
        files = {
            "patent_application_file": (patent_application_file.name, patent_application_file.getvalue(),  patent_application_file.type),
            "office_action_file": (office_action_file.name, office_action_file.getvalue(), office_action_file.type)
        }

        with st.spinner("Extracting text from files..."):

            update_messages = ">> Extracting text from files...\n"
            live_updates.text_area("Live Updates", update_messages, height=300)

            response = requests.post(text_extraction_url, files=files, stream=True)

        if response.status_code == 200:
            update_messages = update_messages + ">> ✅ Text extracted\n\n"
            live_updates.text_area("Live Updates", update_messages, height=300)

            state_schema = response.json()
            return state_schema, update_messages

        else:
            st.error("Failed to extract text.")


def fetching_referenced_patents(state_schema, update_messages):

    time.sleep(1)

    if len(state_schema['references']) > 0:
        update_messages = update_messages + f">> I have found these references in the Office Action: \n{state_schema['references']}\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        time.sleep(1)
        update_messages = update_messages + f">> I will now attempt to fetch them from Google Patents\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        with st.spinner("Fetching referenced patents..."):

            response = requests.post(fetch_references_url, json=state_schema)

        if response.status_code == 200:
            update_messages = update_messages + ">> ✅ Fetched referenced patents\n\n"
            live_updates.text_area("Live Updates", update_messages, height=300)

            state_schema = response.json()

            return state_schema, update_messages

        else:
            st.error("Failed to fetch references.")

    else:
        update_messages = update_messages + f">> No references were found in the Office Action\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)


def retrieve_knowledge_base(state_schema, update_messages):

    time.sleep(1)
    update_messages = update_messages + f">> Retrieving knowledge base...\n"
    live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Retrieving knowledgebase..."):

        response = requests.post(retrieve_knowledge_base_url, json=state_schema)

    if response.status_code == 200:
        update_messages = update_messages + ">> ✅ Retrieved knowledge base\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        state_schema = response.json()

        return state_schema, update_messages

    else:
            st.error("Failed to retrieve knoeledge base.")


def planning_strategy(state_schema, update_messages):

    time.sleep(1)
    update_messages = update_messages + f">> Planning a strategy...\n"
    live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Planning a strategy..."):

        response = requests.post(planning_strategy_url, json=state_schema, stream=True)

    if response.status_code == 200:

        # state_schema = response.json()
        # strategy_text.text_area("Strategy", state_schema['strategy'], height=300)

        def stream():
            strategy_response = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk.decode("utf-8")  # Decode and stream response
                    strategy_response += chunk.decode("utf-8")
                    time.sleep(0.1)

            state_schema['strategy'] = strategy_response
            return strategy_response

        update_messages = update_messages + ">> ✅ I have planned a strategy\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        return stream, state_schema, update_messages

        # return state_schema, update_messages

    else:
        st.error("Failed to plan a strategy.")


def execute_strategy(state_schema, update_messages):

    time.sleep(1)
    update_messages = update_messages + f">> Executing strategy step by step...\n"
    live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Executing the strategy..."):
        response = requests.post(execute_strategy_url, json=state_schema, stream=True)

    if response.status_code == 200:

        # state_schema = response.json()
        # response_text.text_area("Response to OA draft", state_schema['response'], height=300)

        def stream():
            execute_response = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk.decode("utf-8")  # Decode and stream response
                    execute_response += chunk.decode("utf-8")
                    time.sleep(0.1)

            state_schema['response'] = execute_response
            return execute_response

        update_messages = update_messages + ">> ✅ Executed all action steps of the strategy\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        return stream, state_schema, update_messages

        # return state_schema, update_messages

    else:
        st.error("Failed to execute the strategy.")


def generate_draft(state_schema, update_messages):

    time.sleep(1)
    update_messages = update_messages + f">> Editing draft and exporting to a google doc...\n"
    live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Generating a google doc draft..."):
        response = requests.post(generate_draft_url, json=state_schema)

    if response.status_code == 200:
        update_messages = update_messages + ">> ✅ Edited and exported to a google doc\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        state_schema = response.json()

        return state_schema, update_messages

    else:
            st.error("Failed to edit and export to a google doc.")


# Button to start processing
if st.button("Start Processing"):
    live_updates = st.empty()
    draft_text = st.empty()

    state_schema, update_messages = load_files_and_extract_info()
    state_schema, update_messages = fetching_referenced_patents(state_schema, update_messages)
    state_schema, update_messages = retrieve_knowledge_base(state_schema, update_messages)

    # state_schema, update_messages = planning_strategy(state_schema, update_messages)
    with st.chat_message("assistant", avatar="🤖"):
        strategy_response, state_schema, update_messages = planning_strategy(state_schema, update_messages)
        st.markdown("#### Strategy:")
        st.write_stream(strategy_response)
        st.markdown("")

    # state_schema, update_messages = execute_strategy(state_schema, update_messages)
    with st.chat_message("assistant", avatar="🤖"):
        execute_response, state_schema, update_messages = execute_strategy(state_schema, update_messages)
        st.markdown("#### Response to OA draft:")
        st.write_stream(execute_response)
        st.markdown("")

    state_schema, update_messages = generate_draft(state_schema, update_messages)
    draft_text.text_area("The draft that was exported to a google doc:", state_schema['draft'], height=300)
    st.markdown("#### 🎉 The draft has been successfully exported to a google doc! 🎉")

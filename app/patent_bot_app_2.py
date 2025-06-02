import streamlit as st
import json
import requests
import time

st.title("🤖 Patent Bot 📑")
st.markdown("#### Hi Ariel, I'm here to assist you with responding to claim rejections. \
    Upload the desired documents and click the button to get started.")
st.markdown("")

# Uploading the relevant files
patent_application_file = st.file_uploader("Upload the patent application as filed")
recent_claims_file = st.file_uploader("Upload the most recent claims (optional)")
office_action_file = st.file_uploader("Upload the office action")
prior_art_file = st.file_uploader("Upload the prior art (optional)", accept_multiple_files=True)

# Base url and all the endpoints
base_url = "https://response-to-oa-prod-2dkcwif5ra-ew.a.run.app"

text_extraction_url = base_url + "/text_extraction"
fetch_references_url = base_url + "/fetching_references"
retrieve_knowledge_base_url = base_url + "/retrieve_knowledge_base"

respond_to_rejections_url = base_url + "/respond_to_rejections"

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

        if recent_claims_file:
            files["recent_claims_file"] = (recent_claims_file.name, recent_claims_file.getvalue(), recent_claims_file.type)

        if prior_art_file:
            for i, file in enumerate(prior_art_file):
                files[f"prior_art_file_{i+1}"] = (file.name, file.getvalue(), file.type)

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


def respond_to_rejections(state_schema, update_messages):

    time.sleep(1)
    update_messages = update_messages + f">> Responding to claim rejections, this part will take a few minutes...\n"
    live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Responding to claim rejections..."):

        response = requests.post(respond_to_rejections_url, json=state_schema, stream=True)

    if response.status_code == 200:

        state_schema = response.json()

        #strategy_text.text_area("Strategy", state_schema['strategy'], height=300)

        update_messages = update_messages + ">> ✅ I have responded to the claim rejections\n\n"
        live_updates.text_area("Live Updates", update_messages, height=300)

        return state_schema, update_messages

    else:
        st.error("Failed to plan a strategy.")


def select_response(state_schema):

    claim_number = st.session_state.claims_list[st.session_state.claim_iteration]
    original_claim = state_schema['rejected_claims_list'][st.session_state.claim_iteration][claim_number]['original_claim']
    claim_rejection = state_schema['rejected_claims_list'][st.session_state.claim_iteration][claim_number]['rejected_for']
    claim_responses = state_schema['responses'][claim_number]

    claim_presentation = st.empty()

    claim_presentation.text_area(f"Optional responses for {claim_number}" ,
                                 f"This is {claim_number}: \n{original_claim}\n\n\
    It was rejected due to: \n{claim_rejection}\n\n\
    Here are the responses I have prepared for you:\n\
    - 'Amendment': {claim_responses['amend']}.\n\n\
    - 'Dispute': {claim_responses['dispute']}.\n\n\
    Please select one of the responses to proceed:",
    height=400)

    choice = st.radio(
        claim_number,
        ['amend', 'dispute', 'combine', 'remove'],
        key=f"radio {claim_number}",
        index=None
    )

    if choice:
        st.text(f"You selected: {choice}.\nPlease confirm your selection")

        button = st.button("Confirm", key=f"button {claim_number}")
        if button:
            # Save the choice
            st.session_state.your_choices[claim_number] = choice
            state_schema['rejected_claims_list'][st.session_state.claim_iteration][claim_number]['response_type'] = choice
            state_schema['rejected_claims_list'][st.session_state.claim_iteration][claim_number]['chosen_response'] = state_schema['responses'][claim_number][choice]
            st.session_state.schema = state_schema

            # Show confirmation message
            st.text(f"Your response for {claim_number} is {choice}")

            if len(st.session_state.claims_list) > st.session_state.claim_iteration + 1:
                st.session_state.claim_iteration += 1

                placeholder = st.empty()

                text = "Loading next claim rejection"
                for i in range(4):
                    placeholder.markdown(text + " ." * i)
                    time.sleep(0.3)

                st.rerun()

            else:
                st.success("All claim rejections were responded to!")
                st.session_state.claim_iteration += 1
                time.sleep(2)
                st.rerun()
                # st.write("These are your choices:")
                # st.write(st.session_state.your_choices)

            return st.session_state.schema

        return st.session_state.schema

    return st.session_state.schema


def generate_draft(state_schema):

    # time.sleep(1)
    # update_messages = update_messages + f">> Editing draft and exporting to a google doc...\n"
    # live_updates.text_area("Live Updates", update_messages, height=300)

    with st.spinner("Generating a google doc draft..."):
        response = requests.post(generate_draft_url, json=state_schema)

    if response.status_code == 200:
        # update_messages = update_messages + ">> ✅ Edited and exported to a google doc\n\n"
        # live_updates.text_area("Live Updates", update_messages, height=300)

        state_schema = response.json()

        return state_schema

    else:
            st.error("Failed to edit and export to a google doc.")


# ---------------------
# Main logic of the app
# ---------------------
if 'rerun' not in st.session_state:

    # Button to start processing
    if st.button("Start Processing"):
        live_updates = st.empty()
        draft_text = st.empty()

        state_schema, update_messages = load_files_and_extract_info()
        state_schema, update_messages = fetching_referenced_patents(state_schema, update_messages)
        state_schema, update_messages = retrieve_knowledge_base(state_schema, update_messages)
        state_schema, update_messages = respond_to_rejections(state_schema, update_messages)

        st.session_state.schema = state_schema
        st.session_state.claims_list = list(state_schema['responses'].keys())
        st.session_state.claim_iteration = 0
        st.session_state.your_choices = {}
        st.session_state.rerun = True

        st.rerun()
        # st.session_state.schema = select_response(st.session_state.schema)

else:
    if st.session_state.claim_iteration < len(st.session_state.claims_list):
        st.session_state.schema = select_response(st.session_state.schema)

    else:
        st.success("Generating draft...")
        st.session_state.schema = generate_draft(st.session_state.schema)

        show_draft = st.empty()
        show_draft.text_area("The draft that was exported to a google doc:", st.session_state.schema['draft'], height=400)
        st.markdown("#### 🎉 The draft has been successfully exported to a google doc! 🎉")

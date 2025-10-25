import streamlit as st
import os
import uuid
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. Import your compiled agent ---
# This line imports the 'app' variable from your other file.
from Loan_agent import app, Loan_agent_state

# --- 2. Page Setup ---
st.set_page_config(
    page_title="Tata Capital Loan Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("Tata Capital - Personal Loan Agent 🤖")

# --- 3. Setup the Uploads Directory ---
# This is for the salary slip
UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# --- 4. Session State Management ---
# This is the most important part of a Streamlit chat app.
# We need to store the message history and a unique thread_id
# for LangGraph's persistence.

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    print(f"New session started with thread_id: {st.session_state.thread_id}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. The Sidebar for File Uploads ---
with st.sidebar:
    st.header("Income Verification")
    
    # We check the session state for a customer_id
    customer_id = st.session_state.get("customer_id", None)
    
    if not customer_id:
        st.warning("Please verify your phone number in the chat before uploading.")
    else:
        # The file uploader is active if we have a customer_id
        uploaded_file = st.file_uploader(
            f"Upload Salary Slip for Customer {customer_id}",
            type=["pdf"]
        )
        
        if uploaded_file is not None:
            # Define the expected filename
            filename = f"{customer_id}_salary_slip.pdf"
            save_path = os.path.join(UPLOAD_DIRECTORY, filename)
            
            # Save the file to the correct location
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"File saved as {filename}! Please type 'uploaded' in the chat.")

# --- 6. Display Past Chat Messages ---
# Loop through the messages stored in the session state
for message in st.session_state.messages:
    if isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)

# --- 7. The Chat Input Box ---
# This is the text box at the bottom of the screen
if prompt := st.chat_input("Hi, how can I help you?"):
    
    # 1. Add the user's message to the session state
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # 2. Display the user's message in the chat
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 3. Show a "thinking" spinner while the agent works
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            
            # 4. Prepare the input for the agent
            # We only need to send the new human message.
            # The checkpointer will load the full history.
            input_data = {"messages": [HumanMessage(content=prompt)]}
            
            # This config tells LangGraph which conversation thread to use
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            # 5. Call the agent!
            # The .invoke() call will run all the nodes (Sales, Verify, etc.)
            # and only return when the graph hits an END or a wait_for_user.
            final_state = app.invoke(input_data, config=config)
            
            # 6. Extract the agent's last response
            ai_response = final_state["messages"][-1]
            
            # 7. Display the AI's response
            st.markdown(ai_response.content)

    # 8. Update our session state with the full, new history
    # This ensures that if we rerun, we have the complete log.
    st.session_state.messages = final_state["messages"]
    
    # 9. Update the customer_id in our session state if it was found
    if final_state.get("customer_id"):
        st.session_state.customer_id = final_state.get("customer_id")
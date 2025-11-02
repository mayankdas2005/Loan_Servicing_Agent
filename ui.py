import streamlit as st
import os
import uuid
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. Import your compiled agent ---
from Loan_agent import app, Loan_agent_state

# --- 2. Page Setup ---
st.set_page_config(
    page_title="Tata Capital Loan Agent",
    page_icon="🏦",
    layout="wide"
)


# Custom CSS for better appearance
st.markdown("""
    <style>
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Tata Capital - Personal Loan Assistant")
st.markdown("*Your intelligent loan application companion*")

# --- 3. Setup the Uploads Directory ---
UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# --- 4. Session State Management ---
# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    print(f"✨ New session started with thread_id: {st.session_state.thread_id}")

# ✅ FIX 1: Don't duplicate message storage - LangGraph handles it
# We only store metadata here, not the full messages
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

if "loan_approved" not in st.session_state:
    st.session_state.loan_approved = False

# --- 5. Helper Function to Get Current State ---
def get_current_state():
    """
    Retrieves the current state from LangGraph's checkpoint.
    This is the single source of truth.
    """
    try:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        # Get the current state snapshot from the checkpointer
        current_state = app.get_state(config)
        return current_state
    except Exception as e:
        print(f"Error getting state: {e}")
        return None

# --- 6. The Sidebar ---
with st.sidebar:
    st.header("📋 Application Status")
    
    # Display current state information
    current_state = get_current_state()
    
    if current_state and current_state.values:
        state_values = current_state.values
        
        # Show verification status
        if state_values.get("is_verified"):
            st.success("✅ Identity Verified")
            customer_name = state_values.get("customer_details", {}).get("name", "N/A")
            st.info(f"**Customer:** {customer_name}")
            
            # Update session state with customer_id
            if state_values.get("customer_id"):
                st.session_state.customer_id = state_values["customer_id"]
        
        # Show loan approval status
        if state_values.get("loan_approved"):
            st.success("🎉 Loan Approved!")
            st.session_state.loan_approved = True
    
    st.divider()
    
    # --- Income Verification File Upload ---
    st.subheader("📄 Income Verification")
    
    if not st.session_state.customer_id:
        st.warning("⚠️ Please verify your phone number in the chat first.")
    else:
        st.info(f"**Customer ID:** {st.session_state.customer_id}")
        
        uploaded_file = st.file_uploader(
            "Upload Salary Slip (PDF only)",
            type=["pdf"],
            help="Upload your latest salary slip for income verification"
        )
        
        if uploaded_file is not None:
            try:
                # Define the expected filename
                filename = f"{st.session_state.customer_id}_salary_slip.pdf"
                save_path = os.path.join(UPLOAD_DIRECTORY, filename)
                
                # Save the file
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"✅ File saved as `{filename}`")
                st.info("💬 Type **'uploaded'** in the chat to continue.")
                st.session_state.file_uploaded = True
                
            except Exception as e:
                st.error(f"❌ Error saving file: {str(e)}")
    
    st.divider()
    
    # --- Reset Button ---
    if st.button("🔄 Start New Conversation", type="secondary"):
        # Clear the session state
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.customer_id = None
        st.session_state.file_uploaded = False
        st.session_state.conversation_started = False
        st.session_state.loan_approved = False
        st.rerun()

# --- 7. Display Chat Messages ---
# ✅ FIX 2: Get messages from LangGraph state, not session_state
current_state = get_current_state()

if current_state and current_state.values and current_state.values.get("messages"):
    messages = current_state.values["messages"]
    
    # Display all messages except system messages
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("user", avatar="👤"):
                st.markdown(message.content)
else:
    # Show welcome message if no conversation yet
    if not st.session_state.conversation_started:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("👋 Welcome! I'm your Tata Capital loan assistant. How can I help you today?")

# --- 8. The Chat Input Box ---
if prompt := st.chat_input("Type your message here..."):
    
    # Mark conversation as started
    st.session_state.conversation_started = True
    
    # Display the user's message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Show assistant thinking
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                # ✅ FIX 3: Prepare input correctly
                input_data = {"messages": [HumanMessage(content=prompt)]}
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                # Call the agent
                final_state = app.invoke(input_data, config=config)
                
                # ✅ FIX 4: Handle different response types
                if final_state and "messages" in final_state:
                    last_message = final_state["messages"][-1]
                    
                    if isinstance(last_message, AIMessage):
                        response_content = last_message.content
                    else:
                        response_content = str(last_message.content)
                    
                    # Display the response
                    st.markdown(response_content)
                    
                    # ✅ FIX 5: Update session state metadata
                    if final_state.get("customer_id"):
                        st.session_state.customer_id = final_state["customer_id"]
                    
                    if final_state.get("loan_approved"):
                        st.session_state.loan_approved = True
                        st.balloons()  # Celebration effect!
                    
                    # ✅ FIX 6: Check for sanction letter
                    if final_state.get("sanction_letter_path"):
                        letter_path = final_state["sanction_letter_path"]
                        if os.path.exists(letter_path):
                            with open(letter_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📄 Download Sanction Letter",
                                    data=pdf_bytes,
                                    file_name=os.path.basename(letter_path),
                                    mime="application/pdf"
                                )
                else:
                    st.error("❌ Received invalid response from agent.")
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                print(f"Error details: {e}")
                import traceback
                traceback.print_exc()
    
    # ✅ FIX 7: Force a rerun to update the sidebar
    st.rerun()

# --- 9. Footer ---
st.divider()
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8rem;'>
        <p>🔒 Secure & Confidential | Powered by AI | Tata Capital Personal Loans</p>
    </div>
""", unsafe_allow_html=True)

import os
import operator
from typing import TypedDict, Annotated, List, Optional
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from pydantic import BaseModel, Field
import re
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv('api_secret.env')
api_key = os.environ.get('API_KEY')


llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=api_key)


class LoanDetails(BaseModel):
    plan_name: str = Field(description="The name of the loan plan selected.") # <-- ADD THIS LINE
    amount: int = Field(description="The principal amount of the loan.")
    interest_rate: float = Field(description="The annual interest rate (e.g., 8.5).")
    tenure_years: int = Field(description="The loan tenure in years.")

structured_llm = llm.with_structured_output(LoanDetails)


#tools are here 
CRM_API_URL = "http://localhost:8000/crm/verify"
LOAN_API_URL = "http://localhost:8000/loans/options"
LOG_API_URL = "http://localhost:8000/applications/log"
UPLOAD_DIRECTORY = "./uploads/"


@tool
def get_customer_details_tool(phone : str):
    """
    Searches the CRM database for customer details using their phone number.
    Returns a dictionary with customer data if found, or an error if not.
    """
    try:
        response = requests.get(CRM_API_URL, params={'phone': phone})

        if response.status_code == 200:
            print(response)
            return response.json()
        elif response.status_code == 404: 
            print("Tool Error: Customer not found (404)")
            return {"status": "Not Found", "detail": "Customer not found"}
        
        else:
            print(f"Tool Error: API returned status {response.status_code}")
            return {"status": "Error", "detail": f"API server error: {response.text}"}
    
    except requests.ConnectionError as e:
        # This handles the case where the server is not running
        print(f"Tool Error: Connection to CRM server failed. Is server.py running?")
        return {"status": "Error", "detail": "Connection to CRM server failed."}
    
@tool
def get_loan_options_tool(credit_score: int):
    """
    Searches the CRM database for loan options details using their credit scores.
    Returns a dictionary with loan options if found, or an error if not.
    """
    try:
        response = requests.get(LOAN_API_URL, params={'credit_score': credit_score})

        if response.status_code == 200:
            print(response)
            return response.json()
        elif response.status_code == 404: 
            print("Tool Error: Loan options not found (404)")
            return {"status": "Not Found", "options": "Customer not found"}
        
        else:
            print(f"Tool Error: API returned status {response.status_code}")
            return {"status": "Error", "options": f"API server error: {response.text}"}
    
    except requests.ConnectionError as e:
        # This handles the case where the server is not running
        print(f"Tool Error: Connection to CRM server failed. Is server.py running?")
        return {"status": "Error", "": "Connection to CRM server failed."}
    
@tool
def log_application_tool(customer_id: int, plan_name: str, amount: int, interest_rate: float, tenure_years: int) -> dict:
    """
    Logs a finalized loan application to the bank's database via the API.
    """
    print("---TOOL: Logging application to database---")
    payload = {
        "customer_id": customer_id,
        "plan_name": plan_name,
        "amount": amount,
        "interest_rate": interest_rate,
        "tenure_years": tenure_years
    }
    try:
        response = requests.post(LOG_API_URL, json=payload)
        if response.status_code == 200:
            return response.json() # {"status": "success", "application_id": 12345}
        else:
            return {"status": "error", "detail": response.text}
    except Exception as e:
        return {"status": "error", "detail": f"API connection error: {e}"}

# --- 2. Tool to generate the sanction letter PDF ---
PDF_DIRECTORY = "./sanction_letters"

@tool
def generate_sanction_letter_tool(application_id: int, customer_name: str, amount: int, interest_rate: float, tenure_years: int) -> str:
    """
    Generates a simple PDF sanction letter and saves it to a local folder.
    Returns the file path of the generated PDF.
    """
    print("---TOOL: Generating sanction letter PDF---")
    
    # Ensure the directory exists
    if not os.path.exists(PDF_DIRECTORY):
        os.makedirs(PDF_DIRECTORY)
        
    file_path = os.path.join(PDF_DIRECTORY, f"sanction_letter_{application_id}.pdf")
    
    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter # Get page dimensions
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, "TATA CAPITAL - LOAN SANCTION LETTER")
        
        c.setFont("Helvetica", 12)
        c.drawString(72, height - 120, f"Application ID: {application_id}")
        c.drawString(72, height - 140, f"Customer Name: {customer_name}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, height - 180, "Loan Details Approved:")
        
        c.setFont("Helvetica", 12)
        c.drawString(90, height - 200, f"Principal Amount: {amount:,.2f}")
        c.drawString(90, height - 220, f"Interest Rate (APR): {interest_rate:.1f}%")
        c.drawString(90, height - 240, f"Loan Tenure: {tenure_years} years")
        
        c.save()
        print(f"PDF saved to: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return f"Error: Could not generate PDF. {e}"

@tool
def check_file_storage_tool(customer_id: int) -> dict:
    """
    Checks the local file storage to see if a salary slip 
    has been uploaded for a given customer_id.
    
    It looks for a file named '{customer_id}_salary_slip.pdf'.
    """
    print(f"---TOOL: Checking for file for customer {customer_id}---")
    
    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_DIRECTORY):
        print(f"Tool Error: Upload directory '{UPLOAD_DIRECTORY}' does not exist.")
        return {"status": "Error", "detail": "Upload directory not found."}
        
    # Define the expected filename
    expected_filename = f"{customer_id}_salary_slip.pdf"
    file_path = os.path.join(UPLOAD_DIRECTORY, expected_filename)
    
    # Check if the file exists
    if os.path.isfile(file_path):
        print(f"File Found: {file_path}")
        return {"status": "File Found", "path": file_path}
    else:
        print("File Not Found.")
        return {"status": "Not Found"}



#9876543210



class Loan_agent_state(TypedDict):
    #contains message history of both human and agent
    messages : Annotated[List[BaseMessage], operator.add]

    customer_phone : Optional[str]
    customer_details : Optional[dict]
    customer_id : Optional[int]
    credit_score : Optional[int]
    is_verified : bool

    needs_income_proof : Optional[bool]
    is_income_verified : Optional[bool]

    sanction_letter_path : Optional[str]

    routing_decision : str

    presented_options : Optional[List[LoanDetails]]
    selected_loan : Optional[List[LoanDetails]]



# SalesAgent node, this node communicated with the user and learn intent. 
def SalesAgent(state: Loan_agent_state) :
    prompt = "Greet the user, welcoming them to Tata Capital Personal Loan Services"
    
    # Checks if its the first time user is having conversation
    if len(state['messages']) == 1:
        ai_response = llm.invoke(prompt).content
        return {'messages': [AIMessage(content=ai_response)], 'routing_decision':'waiting_for_user'}
    
    #check2
    elif len(state['messages']) > 1:
        last_message = state['messages'][-1].content
        last_message_obj = state['messages'][-1]

        # checking if the customer has been presented with loan options
        # also checking if the customer has selected a loan or not

        if state.get('sanction_letter_path') and not isinstance(last_message_obj, HumanMessage):
            print("---LOGIC: Presenting final sanction letter---")
            
            customer_name = state.get('customer_details', {}).get('name', 'Customer')
            letter_path = state.get('sanction_letter_path')
            
            final_message = (
                f"Congratulations, {customer_name}! Your loan has been approved. \n\n"
                f"You can download your sanction letter here: {letter_path}\n\n"
                "Thank you for choosing Tata Capital!"
            )
            
            return {
                'messages': [AIMessage(content=final_message)],
                'routing_decision': 'end_conversation' # This tells the graph to stop
            }
        
        elif (state.get('needs_income_proof') == True) and \
           (state.get('is_income_verified') == False) and \
           (not isinstance(last_message_obj, HumanMessage)):
            
            print("---LOGIC: Asking user to upload salary slip---")
            customer_name = state.get('customer_details', {}).get('name', 'there')
            amount = state.get('selected_loan').amount
            
            ask_for_upload_msg = (
                f"Hi {customer_name}, to proceed with the ₹{amount:,.0f} loan, I need you to verify your income.\n\n"
                "Please **upload your latest salary slip** (as '{customer_id}_salary_slip.pdf').\n\n"
                "Once you have uploaded the file, please type **'uploaded'** so I can continue."
            )
            return {
                'messages': [AIMessage(content=ask_for_upload_msg)],
                'routing_decision': 'waiting_for_user'
            }

        # --- CHECK 8 (NEW): Did the user just type 'uploaded'? ---
        elif (state.get('needs_income_proof') == True) and \
           ("uploaded" in last_message.lower()):
            
            print("---LOGIC: User typed 'uploaded'. Handing off to income verifier.---")
            return {
                "routing_decision": "goto_income_verification"
            }


        
        elif state.get('presented_options') and not state.get('selected_loan'):
            options_list = state['presented_options']
            
            
            # CHECK 5: The user has replied to the offers.
            if isinstance(last_message_obj, HumanMessage):
                print("---LOGIC: User is making a selection. Handing off to extractor.---")
                return {
                    "routing_decision": "goto_extraction"
                }
            else:
                print("---LOGIC: Presenting loan offers---")
                formatted_options = []
                for i, option in enumerate(options_list):
                    option_str = (
                        f"  {i+1}. A loan of ₹{option.amount:,.0f} "
                        f"at {option.interest_rate:.1f}% "
                        f"for {option.tenure_years} years."
                    )
                    formatted_options.append(option_str)
                
                customer_name = state.get('customer_details', {}).get('name', 'there')
                
                final_message = (
                    f"Great news, {customer_name}! "
                    f"Based on your profile, I've found these options for you:\n\n"
                    f"{'\n'.join(formatted_options)}\n\n"
                    "Please let me know which option you'd like to proceed with (e.g., 'option 1')."
                )
                
                return {
                    'messages': [AIMessage(content=final_message)],
                    'routing_decision': 'waiting_for_user'
                } 
            
        
        #check for phone no if given
        match = re.search(r'\b(\d{10})\b', last_message)

        #if match found we check if they are not verified
        if match and (not state.get('is_verified')):
            ph_no = match.group(1)
            return {'customer_phone': ph_no, 'routing_decision':'goto_verification'}
        
        # if the last message was not phone number, what was it about? 
        # Checking intent in this part of statements

        #if the llm will respond with 'yes' or 'no'
        intent = llm.invoke(f"Does this user want to start a loan application? Respond with 'yes' or 'no': '{last_message}").content.lower().strip()
        
        #intent verified to be 'yes'
        if intent == "yes" and (not state.get('is_verified')) :
            ask_ph_no = llm.invoke("You are a friendly bank agent. The user wants a loan. Ask them for their 10-digit phone number to begin verification.").content 
            return {'messages': [AIMessage(content=ask_ph_no)], 'routing_decision':'waiting_for_user'}
        else:
            general_response = llm.invoke(state['messages']).content
        
            return {
                'messages': [AIMessage(content=general_response)],
                'routing_decision': 'waiting_for_user'
            }




def verification_node(state: Loan_agent_state): 
    # checks phone number and verifies user details 

    phone_to_check = state.get('customer_phone')


    if not phone_to_check:
        print("Verification Error: No phone number in state.")
        return {
            "is_verified": False,
            "routing_decision": "goto_sales_agent"
        }
    
    api_result = get_customer_details_tool.invoke({"phone": phone_to_check})


    if api_result.get('status') == 'Verified':
        customer_data = api_result['data']
        print(f"Verification Success: Found {customer_data['name']}")
        
        # Update the state with all the customer's data
        return {
            "is_verified": True,
            "customer_details": customer_data,
            "customer_id": customer_data['id'],
            "credit_score": customer_data['credit_score'],
            "routing_decision": "goto_underwriting" # Send to the next specialist!
        }
    
    else:
        print(f"Verification Failed: {api_result.get('detail')}")
        
        # Update the state and send back to the SalesAgent to handle
        return {
            "is_verified": False,
            "routing_decision": "goto_sales_agent"
        }
    



def present_offers_node(state: Loan_agent_state):
    credit_score = state.get('credit_score')

    if not credit_score:
        return {'routing_decision': 'goto_sales_agent'}
    
    api_result = get_loan_options_tool.invoke({'credit_score': credit_score})

    if api_result.get('status') == 'Success':
        raw_options = api_result['options']
        structured_options = [LoanDetails(**opt) for opt in raw_options]
        return {'presented_options': structured_options, 'routing_decision': 'goto_sales_agent'}
    else: 
        return {'presented_options': [], 'routing_decision': 'goto_sales_agent'}

    


def extraction_node(state: Loan_agent_state):

    options_list = state.get('presented_options')
    user_reply = state['messages'][-1].content

    if not options_list:
        return {'routing_decision': 'goto_sales_agent'}
    
    else:
        prompt = f"""
You are a loan selection assistant. A user was presented with the following list of loan options:

--- OPTIONS ---
{options_list}
--- END OPTIONS ---

The user then replied with the following message:

--- USER REPLY ---
"{user_reply}"
--- END REPLY ---

Your job is to identify *exactly* which option the user selected from the list. "The second one" refers to the second item in the list, "the 30k one" refers to the option with the amount 30000.

Return the JSON object for *only* the selected loan.
"""
        
        selected_loan_option = structured_llm.invoke(prompt)

        if selected_loan_option:
            return {'selected_loan': selected_loan_option, 'routing_decision': 'goto_income_check'}
        
        else:
            return {'selected_loan': None, 'routing_decision': 'goto_sales_agent'}
        



def sanction_node(state: Loan_agent_state) -> dict:
    
    
    # 1. Get all data from the state
    customer = state.get('customer_details')
    loan = state.get('selected_loan')

    # 2. Paranoia Check
    if not customer or not loan:
        print("Sanction Error: Missing customer or loan data in state.")
        return {"routing_decision": "goto_sales_agent"} # Send back to SalesAgent for error

    # 3. Execute Tool 1: Log the application to the DB
    log_result = log_application_tool.invoke({
        "customer_id": customer['id'],
        "plan_name": loan.plan_name,
        "amount": loan.amount,
        "interest_rate": loan.interest_rate,
        "tenure_years": loan.tenure_years
    })
    
    if log_result.get('status') != 'success':
        print(f"Sanction Error: Failed to log application: {log_result.get('detail')}")
        return {"routing_decision": "goto_sales_agent"}
        
    application_id = log_result.get('application_id')

    # 4. Execute Tool 2: Generate the PDF
    letter_path = generate_sanction_letter_tool.invoke({
        "application_id": application_id,
        "customer_name": customer['name'],
        "amount": loan.amount,
        "interest_rate": loan.interest_rate,
        "tenure_years": loan.tenure_years
    })

    if "Error:" in letter_path:
        print(f"Sanction Error: Failed to generate PDF: {letter_path}")
        return {"routing_decision": "goto_sales_agent"}

    # 5. Success! Update the state with the final path
    print("Sanctioning complete. Handing back to SalesAgent.")
    return {
        "sanction_letter_path": letter_path,
        "routing_decision": "goto_sales_agent" # Hand back for the final message
    }



def income_check_node(state: Loan_agent_state):
    selected_loan_amount = state['selected_loan'].amount
    pre_approval_limit = state['customer_details']['pre_approved_limit']


    if not state.get('selected_loan') or not state.get('customer_details'):
        return {'routing_decision': 'goto_sales_agent'}
    
    else:
        if selected_loan_amount <= pre_approval_limit:
            return {'is_income_verified': True, 'routing_decision': 'goto_sanctioning'}
        elif selected_loan_amount > pre_approval_limit and selected_loan_amount <= (2 * pre_approval_limit):
            return {'needs_income_proof': True, 'is_income_verified': False, 'routing_decision': 'goto_sales_agent'}
        else:
            {"selected_loan": None, "routing_decision": "goto_sales_agent"}





def verify_income_node(state: Loan_agent_state) -> dict:
    """
    The Income Verification specialist. It uses the 
    check_file_storage_tool to verify the user's uploaded file.
    """
    print("---NODE: VerifyIncomeNode---")
    
    # 1. Get the customer_id from the state
    customer_id = state.get('customer_id')
    
    # 2. Paranoia Check
    if not customer_id:
        print("Income Verify Error: Missing customer_id in state.")
        return {"routing_decision": "goto_sales_agent"}

    # 3. Execute the tool
    file_check_result = check_file_storage_tool.invoke({"customer_id": customer_id})
    
    # 4. Process the result
    
    # Case 1: SUCCESS
    if file_check_result.get('status') == 'File Found':
        print("Income Verification Success: File was found.")
        
        # Update the state flags and route to final sanctioning
        return {
            "is_income_verified": True,
            "needs_income_proof": False, # We no longer need proof
            "routing_decision": "goto_sanctioning"
        }
    
    # Case 2: FAILURE (Not Found or Error)
    else:
        print("Income Verification Failed: File not found.")
        
        # Update state and send back to SalesAgent to ask the user again
        return {
            "routing_decision": "goto_sales_agent"
        }
    



# --- 1. Define the Simple Router Functions ---
# These functions just read the 'routing_decision' from the state.

def sales_agent_router(state: Loan_agent_state) -> str:
    """The main router. Reads the decision from the SalesAgent."""
    decision = state.get("routing_decision")
    print(f"---ROUTER (SalesAgent): --> {decision} ---")
    return decision

def verification_router(state: Loan_agent_state) -> str:
    """Routes after the VerificationAgent runs."""
    decision = state.get("routing_decision")
    print(f"---ROUTER (Verification): --> {decision} ---")
    return decision

def extraction_router(state: Loan_agent_state) -> str:
    """Routes after the ExtractionAgent runs."""
    decision = state.get("routing_decision")
    print(f"---ROUTER (Extraction): --> {decision} ---")
    return decision
    
def income_check_router(state: Loan_agent_state) -> str:
    """Routes after the IncomeCheckAgent runs."""
    decision = state.get("routing_decision")
    print(f"---ROUTER (IncomeCheck): --> {decision} ---")
    return decision

def income_verify_router(state: Loan_agent_state) -> str:
    """Routes after the IncomeVerification (file check) agent runs."""
    decision = state.get("routing_decision")
    print(f"---ROUTER (IncomeVerify): --> {decision} ---")
    return decision

# --- 2. Assemble the Graph ---

print("Assembling the agent graph...")
workflow = StateGraph(Loan_agent_state)

# --- 3. Add All Nodes ---
workflow.add_node("sales_agent", SalesAgent)
workflow.add_node("verify_customer", verification_node)
workflow.add_node("present_offers", present_offers_node)
workflow.add_node("extract_choice", extraction_node)
workflow.add_node("check_income_policy", income_check_node)
workflow.add_node("verify_uploaded_income", verify_income_node)
workflow.add_node("generate_sanction", sanction_node)

# --- 4. Set the Entry Point ---
# All conversations start with the SalesAgent.
workflow.set_entry_point("sales_agent")

# --- 5. Add All Edges ---

# The main "Hub" router (from the SalesAgent)
workflow.add_conditional_edges(
    "sales_agent",
    sales_agent_router,
    {
        "waiting_for_user": END,  # Stop and wait for the next human input
        "goto_verification": "verify_customer",
        "goto_extraction": "extract_choice",
        "goto_income_verification": "verify_uploaded_income",
        "end_conversation": END # The process is finished
    }
)

# Router for the VerificationAgent
workflow.add_conditional_edges(
    "verify_customer",
    verification_router,
    {
        "goto_underwriting": "present_offers", # Success
        "goto_sales_agent": "sales_agent"     # Failure
    }
)

# Router for the ExtractionAgent
workflow.add_conditional_edges(
    "extract_choice",
    extraction_router,
    {
        "goto_income_check": "check_income_policy", # Success
        "goto_sales_agent": "sales_agent"        # Failure
    }
)

# Router for the IncomeCheckAgent (Policy Check)
workflow.add_conditional_edges(
    "check_income_policy",
    income_check_router,
    {
        "goto_sanctioning": "generate_sanction", # Approved!
        "goto_sales_agent": "sales_agent"        # Needs upload or is rejected
    }
)

# Router for the VerifyIncomeNode (File Check)
workflow.add_conditional_edges(
    "verify_uploaded_income",
    income_verify_router,
    {
        "goto_sanctioning": "generate_sanction", # File found, approved!
        "goto_sales_agent": "sales_agent"        # File not found
    }
)

# Simple edges for nodes that have only one possible next step
workflow.add_edge("present_offers", "sales_agent")
workflow.add_edge("generate_sanction", "sales_agent")


conn = sqlite3.connect("memory.db", check_same_thread=False)

# 2. Instantiate the SqliteSaver directly with the connection
memory = SqliteSaver(conn=conn)

# 3. Now, compile the app with the *real* saver object
app = workflow.compile(checkpointer=memory)

print("Graph compiled successfully.")


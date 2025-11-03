import os
from pathlib import Path
import operator
from typing import TypedDict, Annotated, List, Optional, Union
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts.chat import BaseChatPromptTemplate, BaseStringMessagePromptTemplate
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
import uuid
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime

load_dotenv('api_secret.env')
api_key = os.environ.get('API_KEY')


llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=api_key)

# Structuring llm for giving exactly the loan details
class LoanDetails(BaseModel):
    plan_name: str = Field(description="The name of the loan plan selected.") # <-- ADD THIS LINE
    amount: int = Field(description="The principle amount of the loan.")
    interest_rate: float = Field(description="The annual interest rate (e.g., 8.5).")
    tenure_years: int = Field(description="The loan tenure in years.")

structured_llm = llm.with_structured_output(LoanDetails)


class AddNewCustomer(BaseModel):
    customer_name: str
    customer_phone : str
    customer_address : str
    credit_score : int
    pin : str

customer_data_llm = llm.with_structured_output(AddNewCustomer)


#Tools are here 
CRM_API_URL = "http://localhost:8000/crm/verify"
LOAN_API_URL = "http://localhost:8000/loans/options"
LOG_API_URL = "http://localhost:8000/applications2/log"
FETCH_APPLICATION_URL = "http://localhost:8000/applications2"
ADD_CUSTOMER_URL = "http://localhost:8000/add_customer"
UPLOAD_DIRECTORY = "./uploads/"

@tool
def get_customer_details_tool(phone : str, pin : str):
    """
    Searches the CRM database for customer details using their phone number.
    Returns a dictionary with customer data if found, or an error if not.
    """
    try:
        response = requests.get(CRM_API_URL, params={'phone': phone, 'pin': pin})

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
def log_application_tool(customer_id: int, plan_name: str, amount: int, interest_rate: float, tenure_years: int , application_id: str) -> dict:
    """
    Logs a finalized loan application to the bank's database via the API.
    """
    print("---TOOL: Logging application to database---")
    payload = {
        "application_id": application_id,
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
def generate_sanction_letter_tool(
    application_id: int, 
    customer_name: str, 
    amount: int, 
    interest_rate: float, 
    tenure_years: int,
    amortization_data: Optional[dict]
) -> str:
    """
    Generates a professional PDF sanction letter with a complete amortization schedule table.
    Returns the file path of the generated PDF.
    """
    print("---TOOL: Generating enhanced sanction letter PDF with amortization table---")
    
    # Ensure directory exists
    if not os.path.exists(PDF_DIRECTORY):
        os.makedirs(PDF_DIRECTORY)
        
    file_path = os.path.join(PDF_DIRECTORY, f"sanction_letter_{application_id}.pdf")
    
    try:
        # Create the PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Container for PDF elements
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5f3d'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        normal_style.spaceAfter = 10
        
        # Title
        title = Paragraph("<b>TATA CAPITAL</b><br/>LOAN SANCTION LETTER", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Application Details
        app_details_data = [
            ['Application ID:', str(application_id), 'Date:', datetime.now().strftime('%d-%b-%Y')],
            ['Customer Name:', customer_name, 'Loan Type:', 'Personal Loan']
        ]
        
        app_table = Table(app_details_data, colWidths=[100, 150, 80, 120])
        app_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5f3d')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2c5f3d')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(app_table)
        elements.append(Spacer(1, 20))
        
        # Congratulations message
        congrats = Paragraph(
            f"Dear <b>{customer_name}</b>,<br/><br/>"
            "We are pleased to inform you that your loan application has been <b>APPROVED</b>. "
            "Below are the details of your sanctioned loan:",
            normal_style
        )
        elements.append(congrats)
        elements.append(Spacer(1, 15))
        
        # Loan Summary Table
        summary_heading = Paragraph("<b>LOAN SUMMARY</b>", heading_style)
        elements.append(summary_heading)
        
        monthly_payment = amortization_data['monthly_payment']
        total_payment = amortization_data['total_payment']
        total_interest = amortization_data['total_interest']
        
        loan_summary_data = [
            ['Principle Amount', f'₹{amount:,.2f}'],
            ['Interest Rate (p.a.)', f'{interest_rate}%'],
            ['Loan Tenure', f'{tenure_years} years ({tenure_years * 12} months)'],
            ['Monthly EMI', f'₹{monthly_payment:,.2f}'],
            ['Total Amount Payable', f'₹{total_payment:,.2f}'],
            ['Total Interest Payable', f'₹{total_interest:,.2f}']
        ]
        
        summary_table = Table(loan_summary_data, colWidths=[250, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a472a')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c8e6c9')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f1f8f4')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 25))
        
        # Amortization Schedule Heading
        amort_heading = Paragraph("<b>AMORTIZATION SCHEDULE</b>", heading_style)
        elements.append(amort_heading)
        elements.append(Spacer(1, 10))
        
        # Create amortization table data
        schedule = amortization_data['schedule']
        
        # Table headers
        amort_data = [
            ['Month', 'EMI Payment', 'Principle', 'Interest', 'Balance']
        ]
        
        # Add all schedule rows
        for item in schedule:
            amort_data.append([
                str(item['month']),
                f"₹{item['payment']:,.2f}",
                f"₹{item['principle']:,.2f}",
                f"₹{item['interest']:,.2f}",
                f"₹{item['balance']:,.2f}"
            ])
        
        # Create the amortization table
        amort_table = Table(
            amort_data,
            colWidths=[60, 100, 100, 100, 100],
            repeatRows=1  # Repeat header on each page
        )
        
        # Style the amortization table
        amort_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a472a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Month column centered
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Amount columns right-aligned
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1a472a')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            
            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(amort_table)
        elements.append(Spacer(1, 20))
        
        # Footer section
        footer_text = Paragraph(
            "<b>Terms and Conditions:</b><br/>"
            "1. The loan amount will be disbursed to your registered bank account within 3-5 business days.<br/>"
            "2. EMI payments are due on the same date each month.<br/>"
            "3. Late payment charges of 2% per month will apply for overdue payments.<br/>"
            "4. No prepayment penalty for payments made after 6 months.<br/><br/>"
            "<b>For any queries, please contact:</b><br/>"
            "Customer Care: 1800-209-8800 | Email: support@tatacapital.com<br/><br/>"
            "Thank you for choosing Tata Capital!",
            normal_style
        )
        elements.append(footer_text)
        
        # Build the PDF
        doc.build(elements)
        
        print(f"Enhanced PDF saved to: {file_path}")
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

@tool
def calculate_amortization_schedule_tool(amount: int, interest_rate: float, tenure_years: int) -> dict:
    """Calculates the whole loan amortization schedule for each month,
    showing how much money is going towards interest and how much towards principle"""

    print('---------Calculating amortization schedule---------')
    try:
        monthly_rate = interest_rate/100/12
        total_months = tenure_years*12
        monthly_payment = amount*(monthly_rate*(1+monthly_rate)**total_months)/((monthly_rate*((1+monthly_rate)**total_months))-1)

        schedule = []
        total_interest = 0
        balance = amount

        for i in  range(1, total_months+1):
            monthly_interest_payment = balance*monthly_rate
            monthly_principle_payment = monthly_payment - monthly_interest_payment
            balance -= monthly_principle_payment
            total_interest += monthly_interest_payment

            if i == total_months:
                    monthly_principle_payment += balance
                    balance = 0

            schedule.append({
                'month': i,
                'payment': round(monthly_payment, 2),
                'interest': round(monthly_interest_payment, 2),
                'principle': round(monthly_principle_payment, 2),
                'balance': round(balance, 2)
            })
        result =  {
                "status": "success",
                "monthly_payment": round(monthly_payment, 2),
                "total_payment": round(monthly_payment * total_months, 2),
                "total_interest": round(total_interest, 2),
                "schedule": schedule
            }

        print(f"---DEBUG: Amortization calculated successfully. Monthly: ₹{result['monthly_payment']}---")
        return result
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@tool
def get_loan_detail_tool(application_id: str):
    """
    Retrieves loan details from the database for a given application ID.
    This allows users to query their existing loans.
    """
    try:
        response = requests.get(FETCH_APPLICATION_URL, params=application_id)
        if response.status_code == 200:
            return {'status': 'success', 'loan': response.json()}
        else:
            return {'status': 'not_found', 'detail': 'loan_not_found'}

    except Exception as e:
        return {'status': 'error', 'details': str(e)}
     
@tool
def add_new_customer_tool(name: str, phone: str, address: str, credit_score: int, pin: str , pre_approved_limit: int ) -> dict :
    """Adds a new customer with all their detals in to the database, making a new account for them"""

    print('-----TOOL Adding customer---------')
    payload = {
        'customer_name' : name,
        'customer_phone' : phone,
        'customer_address' : address, 
        'pre_approved_limit' : pre_approved_limit,
        'credit_score': credit_score,
        'pin' : pin
    }

    try:
        response = requests.post(ADD_CUSTOMER_URL, json=payload)
        if response.status_code == 200:
            return response.json()
        
        else:
            return {'status': 'error', 'details': response.text}
        
    except Exception as e:
        return {"status": "error", "detail": f"API connection error: {e}"}
        
        

class Loan_agent_state(TypedDict):
    #contains message history of both human and agent
    messages : Annotated[List[Union[BaseMessage,BaseStringMessagePromptTemplate, BaseChatPromptTemplate]], operator.add]

    customer_phone : Optional[str]
    customer_pin : Optional[str]
    customer_details : Optional[dict]
    customer_id : Optional[int]
    credit_score : Optional[int]
    is_verified : bool
    upload_failed_attempts: int

    is_existing : Optional[bool]
    awaiting_registration_details : bool
    registration_attempt : int

    needs_income_proof : Optional[bool]
    is_income_verified : Optional[bool]

    sanction_letter_path : Optional[str]

    routing_decision : str

    presented_options : Optional[List[LoanDetails]]
    selected_loan : Optional[LoanDetails]
    offers_just_presented : Optional[bool]

    application_id : Optional[str]
    loan_approved: Optional[bool]
    amortization_schedule : Optional[dict]
    conversation_mode : str



# SalesAgent node, this node communicated with the user and learn intent. 
def SalesAgent(state: Loan_agent_state):
    """
    Main conversational agent that handles user interaction and routing.
    """
    # Prevent extremely long conversations
    if len(state['messages']) > 60:
        reset_msg = (
            "I notice we've been chatting for quite a while! "
            "Let's start fresh. How can I help you with a personal loan today?"
        )
        return {
            'messages': [AIMessage(content=reset_msg)],
            'routing_decision': 'waiting_for_user'
        }
    
    # CHECK 0: Determine if we need to ask about existing customer status
    if state.get('is_existing') is None:  # ← Not yet determined
        print("---LOGIC: Need to determine if customer is existing or new---")
        
        last_message_obj = state['messages'][-1]
        
        # First message - just greet
        if len(state['messages']) == 1:
            print("---LOGIC: First interaction, greeting user---")
            greeting_msg = (
                "👋 Hello! Welcome to Tata Capital. I'm Alex, your personal loan assistant.\n\n"
                "Are you an existing Tata Capital customer?"
            )
            return {
                'messages': [AIMessage(content=greeting_msg)], 
                'routing_decision': 'waiting_for_user'
            }
        
        # User has responded to greeting - check if they're existing or new
        elif isinstance(last_message_obj, HumanMessage):
            message_lower = last_message_obj.content.lower()
            
            # User says YES - they're existing
            if any(word in message_lower for word in ['yes', 'i am', 'existing', 'have account', 'already']):
                print("---LOGIC: User is existing customer---")
                
                ask_details_msg = (
                    "Great! I'd love to help you with a loan.\n\n"
                    "Could you please provide:\n"
                    "1. Your 10-digit phone number\n"
                    "2. Your 4-digit PIN\n\n"
                    "This will help me verify your account."
                )
                
                return {
                    'messages': [AIMessage(content=ask_details_msg)],
                    'is_existing': True,
                    'routing_decision': 'waiting_for_user'
                }
            
            # User says NO - they're new
            elif any(word in message_lower for word in ['no', 'not', 'new', 'don\'t', 'no account', 'first time']):
                print("---LOGIC: User is NEW customer---")
                
                ask_registration_msg = (
                    "No problem! I'd be happy to help you get started with Tata Capital.\n\n"
                    "Would you like me to create an account for you right now?"
                )
                
                return {
                    'messages': [AIMessage(content=ask_registration_msg)],
                    'is_existing': False,  # ⭐ SET THIS!
                    'routing_decision': 'waiting_for_user'
                }
            
            # User didn't give a clear answer
            else:
                clarify_msg = "Could you please clarify - are you an existing Tata Capital customer? (Yes/No)"
                return {
                    'messages': [AIMessage(content=clarify_msg)],
                    'routing_decision': 'waiting_for_user'
                }
    
    # For all subsequent checks, we need the last message
    last_message_obj = state['messages'][-1]
    last_message = last_message_obj.content
    
    # CHECK 1: First time interaction - greet the user
    if len(state['messages']) == 1:
        print("---LOGIC: First interaction, greeting user---")
        prompt = (
            "You are a friendly Tata Capital bank agent. "
            "Greet the user warmly and introduce yourself as their personal loan assistant. "
            "Keep it brief and welcoming."
            "Ask if the user is an existing customer of Tata Capital"
        )
        ai_response = llm.invoke(prompt).content
        return {
            'messages': [AIMessage(content=ai_response)], 
            'routing_decision': 'waiting_for_user'
        }

    # For all subsequent checks, we need the last message
    last_message_obj = state['messages'][-1]
    last_message = last_message_obj.content
    


    # Checking is user is an existing customer 
    if (state.get('is_existing') == False) and isinstance(last_message_obj, HumanMessage):
        
        # Check if user wants to register
        if any(word in last_message.lower() for word in ['yes', 'sure', 'okay', 'register', 'sign up', 'create']):
            print("---LOGIC: User wants to register. Asking for details---")
            
            registration_prompt = (
                "Perfect! Let's get you registered. I'll need the following information:\n\n"
                "1. **Full Name**\n"
                "2. **Address**\n"
                "3. **Credit Score** (if you know it, otherwise I'll estimate 650)\n"
                "4. **4-digit PIN** (for secure login)\n\n"
                "Please provide all details in one message. For example:\n"
                "\"My name is John Doe,My phone number is 9087033224, I live at 123 Main St Chennai, my credit score is 720, and my PIN is 1234\""
            )

            return {
                'messages': [AIMessage(content=registration_prompt)],
                'awaiting_registration_details': True,
                'routing_decision': 'waiting_for_user'
            }
        
        elif any(word in last_message.lower() for word in ['no', 'not now', 'cancel']):
            print("---LOGIC: User declined registration---")
            
            decline_msg = (
                "No problem! If you'd like to apply for a loan in the future, "
                "just come back and we'll help you get registered. Have a great day!"
            )
            
            return {
                'messages': [AIMessage(content=decline_msg)],
                'routing_decision': 'end_conversation'
            }
        
    if state.get('awaiting_registration_details') and isinstance(last_message_obj, HumanMessage):
        print("---LOGIC: User provided registration details. Routing to registration node---")
        return {"routing_decision": "goto_registration"}
            
            
        


    # Debugging 
    """print("Before CHECK 2: Post approval and displaying sanction_letter ")
    if not isinstance(last_message_obj, HumanMessage):
        print("AI message before")
    else:
        print("Human Message")"""

    
    # CHECK 2: Post-approval - sanction letter ready
    if state.get('sanction_letter_path') and not isinstance(last_message_obj, AIMessage):
        print("---LOGIC: Presenting final sanction letter---")
        
        customer_name = state.get('customer_details', {}).get('name', 'Customer')
        letter_path = state.get('sanction_letter_path')
        
        final_message = (
            f"Congratulations, {customer_name}! Your loan has been approved. 🎉\n\n"
            f"📄 You can download your sanction letter here: {letter_path}\n\n"
            "The letter includes your complete amortization schedule.\n\n"
            "You can now ask me questions like:\n"
            "- 'Show me the amortization schedule'\n"
            "- 'What's my monthly payment?'\n"
            "- 'Give me a loan summary'\n\n"
            "Thank you for choosing Tata Capital!"
        )
        
        return {
            'messages': [AIMessage(content=final_message)],
            'routing_decision': 'waiting_for_user'  # Continue conversation
        }
    
    # CHECK 3: Post-approval - handle loan queries
    if state.get('loan_approved') and isinstance(last_message_obj, HumanMessage):
        print("---LOGIC: Loan approved, checking for loan queries---")
        
        query_keywords = ['schedule', 'payment', 'amortization', 'balance', 
                         'interest', 'summary', 'how much', 'monthly', 'emi']
        
        if any(keyword in last_message.lower() for keyword in query_keywords):
            print("---LOGIC: Detected loan query, routing to query handler---")
            return {"routing_decision": "goto_loan_query"}
    
    from pathlib import Path

    # CHECK 4: Income proof needed - ask for upload
    if (state.get('needs_income_proof') == True) and \
    (state.get('is_income_verified') == False) and \
    (not isinstance(last_message_obj, HumanMessage)):
        
        print("---LOGIC: Asking user to upload salary slip---")
        customer_name = state.get('customer_details', {}).get('name', 'there')
        customer_id = state.get('customer_id')
        amount = state.get('selected_loan').amount
        
        ask_for_upload_msg = (
            f"Hi {customer_name}, to proceed with the ₹{amount:,.0f} loan, I need you to verify your income.\n\n"
            f"Please **upload your latest salary slip** as '{customer_id}_salary_slip.pdf' to the uploads folder.\n\n"
            "Once you have uploaded the file, please type **'uploaded'** so I can continue."
        )
        return {
            'messages': [AIMessage(content=ask_for_upload_msg)],
            'routing_decision': 'waiting_for_user'
        }

    # CHECK 5: User typed 'uploaded' - VALIDATE FILE EXISTS
    if (state.get('needs_income_proof') == True) and \
    isinstance(last_message_obj, HumanMessage) and \
    ("uploaded" in last_message.lower()):
        
        print("---LOGIC: User typed 'uploaded'. Checking for file---")
        
        customer_id = state.get('customer_id')
        uploads_dir = Path('uploads')
        expected_file = uploads_dir / f"{customer_id}_salary_slip.pdf"
        
        # ✅ CHECK: Does the file actually exist?
        if expected_file.exists():
            print(f"✅ File found: {expected_file}")
            return {
                "routing_decision": "goto_income_verification"
            }
        
        else:
            print(f"❌ File not found: {expected_file}")
            
            # Track failed attempts
            failed_attempts = state.get('upload_failed_attempts', 0)
            
            # After 3 failed attempts, escalate
            if failed_attempts >= 2:
                print("❌ User exceeded maximum upload attempts")
                
                escalation_msg = (
                    "I've tried to locate your salary slip multiple times without success.\n\n"
                    "Let me connect you with a support agent who can help you upload it manually.\n\n"
                    "**Support team will contact you shortly.**"
                )
                
                return {
                    'messages': [AIMessage(content=escalation_msg)],
                    'routing_decision': 'end_conversation'
                }
            
            else:
                # File doesn't exist - ask again
                error_msg = (
                    f"❌ I couldn't find your salary slip file (Attempt {failed_attempts + 1}/3).\n\n"
                    f"Please make sure to upload the file as **'{customer_id}_salary_slip.pdf'** "
                    f"to the **'uploads'** folder.\n\n"
                    "Make sure the filename is **exactly correct**, then type 'uploaded' again."
                )
                
                return {
                    'messages': [AIMessage(content=error_msg)],
                    'upload_failed_attempts': failed_attempts + 1,
                    'routing_decision': 'waiting_for_user'
                }


    # CHECK 6: Loan options just presented
    if state.get('presented_options') and not state.get('selected_loan'):
        options_list = state['presented_options']
        
        # Present offers to user
        if state.get('offers_just_presented'):
            print("---LOGIC: Presenting loan offers to user---")
            formatted_options = []
            for i, option in enumerate(options_list, 1):
                option_str = (
                    f"  {i}. ₹{option.amount:,.0f} "
                    f"at {option.interest_rate:.1f}% interest "
                    f"for {option.tenure_years} years"
                )
                formatted_options.append(option_str)
            
            customer_name = state.get('customer_details', {}).get('name', 'there')
            
            final_message = (
                f"Great news, {customer_name}! "
                f"Based on your credit profile, here are your loan options:\n\n"
                f"{chr(10).join(formatted_options)}\n\n"
                "Please let me know which option you'd like (e.g., 'I'll take option 1')."
            )
            
            return {
                'messages': [AIMessage(content=final_message)],
                'offers_just_presented': False,
                'routing_decision': 'waiting_for_user'
            }
        
        # User is making a selection
        elif isinstance(last_message_obj, HumanMessage):
            print("---LOGIC: User is making a selection. Handing off to extractor.---")
            return {
                "routing_decision": "goto_extraction"
            }
    
    # CHECK 7: Look for phone number and pin in message
    if not state.get('is_verified'):
        phone_match = re.search(r'\b(\d{10})\b', last_message)
        pin_match = re.search(r'\b(\d{4})\b', last_message)
        
        if phone_match and pin_match:
            print(f"---LOGIC: Phone number detected: {phone_match.group(1)}---")
            ph_no = phone_match.group(1)
            pin_no = pin_match.group(1)
            return {
                'customer_phone': ph_no, 
                'customer_pin' : pin_no,
                'routing_decision': 'goto_verification'
            }
    
    # CHECK 8: Check for loan intent keywords
    if not state.get('is_verified') and isinstance(last_message_obj, HumanMessage):
        loan_keywords = ['loan', 'finance', 'credit', 'need money', 'borrow', 'apply']
        message_lower = last_message.lower()
        
        has_loan_keyword = any(keyword in message_lower for keyword in loan_keywords)
        
        if has_loan_keyword:
            print("---LOGIC: Loan keyword detected, verifying intent with LLM---")
            
            intent_check_prompt = f"""Analyze if the user wants to apply for a loan.

User message: "{last_message}"

Important: 
- If they say they DON'T want a loan or are refusing, respond with 'NO'
- If they are asking about loans positively or want to apply, respond with 'YES'
- If they're just asking general questions, respond with 'NO'

Respond with ONLY 'YES' or 'NO'."""
            
            intent_response = llm.invoke(intent_check_prompt).content.upper().strip()
            print(f"---DEBUG: Intent response: '{intent_response}'---")
            
            if 'YES' in intent_response:
                print("---LOGIC: User wants a loan. Asking for phone number and pin ---")
                ask_ph_no = (
                    "Great! I'd be happy to help you with a personal loan. "
                    "To get started, could you please provide your 10-digit phone number and your 4-digit pin?"
                )
                return {
                    'messages': [AIMessage(content=ask_ph_no)], 
                    'routing_decision': 'waiting_for_user'
                }
            else:
                print("---LOGIC: Intent verified as NO---")
                polite_response = (
                    "I understand. I'm here to help with any questions about personal loans "
                    "whenever you're ready. Is there anything else I can assist you with today?"
                )
                return {
                    'messages': [AIMessage(content=polite_response)], 
                    'routing_decision': 'waiting_for_user'
                }
    
    # FALLBACK: General conversation
    print("---FALLBACK: General Chat---")
    
    try:
        # Create a conversational prompt
        chat_prompt = f"""You are a friendly and helpful Tata Capital bank agent named Alex. 
A customer just said: "{last_message}"

Respond naturally, warmly, and helpfully. Keep your response concise (2-3 sentences).
If it's a greeting, respond warmly and ask how you can help with personal loans.
Stay professional but friendly."""
        
        # Get the LLM response - extract .content immediately
        llm_response = llm.invoke(chat_prompt)
        general_response = llm_response.content  # ← CRITICAL: Extract content here!
        
        print(f"---DEBUG: Generated response: {general_response[:50]}...---")
        
        return {
            'messages': [AIMessage(content=general_response)],
            'routing_decision': 'waiting_for_user'
        }
        
    except Exception as e:
        print(f"ERROR during fallback LLM invoke: {e}")
        return {
            'messages': [AIMessage(content="Sorry, I encountered an issue. Could you please repeat that?")],
            'routing_decision': 'waiting_for_user'
        }


def verification_node(state: Loan_agent_state): 
    # checks phone number and pin and verifies user details 

    phone_to_check = state.get('customer_phone')
    pin_to_check = state.get('customer_pin')


    if not phone_to_check or not pin_to_check:
        print("Verification Error: No phone number or pin number in state.")
        return {
            "is_verified": False,
            "routing_decision": "goto_sales_agent"
        }
    
    api_result = get_customer_details_tool.invoke({"phone": phone_to_check, "pin": pin_to_check})


    if api_result.get('status') == 'Verified':
        customer_data = api_result['data']
        print(f"Verification Success: Found {customer_data['name']}")
        
        # Update the state with all the customer's data
        return {
            "is_verified": True,
            "is_existing" : True,
            "customer_details": customer_data,
            "customer_id": customer_data['id'],
            "credit_score": customer_data['credit_score'],
            "routing_decision": "goto_underwriting" # Send to the next specialist!
        }
    
    else:
        print(f"Verification Failed: {api_result.get('detail')}")
        ask_registration_msg = (
            f"I couldn't find an account with phone number {phone_to_check}.\n\n"
            "Would you like to create a new account? Just say **'yes'** and I'll help you register!"
        )
        
        # Update the state and send back to the SalesAgent to handle
        return {
            "is_verified": False,
            "is_existing" : False,
            "messages" : [AIMessage(content=ask_registration_msg)],
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
        return {
            'presented_options': structured_options,
            'offers_just_presented': True, 
            'routing_decision': 'goto_sales_agent'
            }
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
    amortization_data = state.get('amortization_schedule')
    # Create a unique loan application id
    application_id = str(uuid.uuid4())


    # 2. Paranoia Check
    if not customer or not loan:
        print("Sanction Error: Missing customer or loan data in state.")
        return {"routing_decision": "goto_sales_agent"} # Send back to SalesAgent for error

    # 3. Execute Tool 1: Log the application to the DB
    log_result = log_application_tool.invoke({
        "application_id": application_id,
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
        "tenure_years": loan.tenure_years,
        "amortization_data": amortization_data
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
    """
    Checks if loan amount exceeds pre-approved limit.
    If yes, routes to income verification; if no, proceeds to sanctioning.
    """
    print("---NODE: IncomeCheckNode---")
    
    selected_loan_amount = state['selected_loan'].amount
    pre_approval_limit = state['customer_details']['pre_approved_limit']
    
    print(f"Loan: ₹{selected_loan_amount}, Pre-approval: ₹{pre_approval_limit}")
    
    if not state.get('selected_loan') or not state.get('customer_details'):
        print("❌ Missing loan or customer details")
        return {'routing_decision': 'goto_sales_agent'}
    
    # Case 1: Loan within pre-approval limit - proceed directly to sanctioning
    if selected_loan_amount <= pre_approval_limit:
        print("---LOGIC: Loan within pre-approval limit. Proceeding to sanctioning---")
        return {
            'is_income_verified': True,
            'needs_income_proof': False,
            'routing_decision': 'goto_sanctioning'  # ✅ Direct to sanctioning
        }
    
    # Case 2: Loan exceeds pre-approval but within 2x - need income proof
    elif selected_loan_amount <= (2 * pre_approval_limit):
        print("---LOGIC: Loan exceeds pre-approval. Asking for income proof---")
        
        customer_name = state.get('customer_details', {}).get('name', 'there')
        customer_id = state.get('customer_id')
        
        ask_income_msg = (
            f"Hi {customer_name}, the loan amount (₹{selected_loan_amount:,.0f}) exceeds your "
            f"pre-approved limit (₹{pre_approval_limit:,.0f}).\n\n"
            f"To proceed, I need to verify your income.\n\n"
            f"Please upload your latest **salary slip** as '{customer_id}_salary_slip.pdf'.\n\n"
            "Once uploaded, type **'uploaded'** to continue."
        )
        
        return {
            'messages': [AIMessage(content=ask_income_msg)],
            'needs_income_proof': True,
            'is_income_verified': False,
            'routing_decision': 'waiting_for_user'  # ✅ Wait for upload, not back to sales_agent!
        }
    
    # Case 3: Loan way too high - reject and ask to select again
    else:
        print("---LOGIC: Loan exceeds maximum limit (2x pre-approval)---")
        
        max_loan = 2 * pre_approval_limit
        reject_msg = (
            f"Sorry, the requested loan amount (₹{selected_loan_amount:,.0f}) exceeds our maximum "
            f"lending limit for you (₹{max_loan:,.0f}).\n\n"
            f"Would you like to select a different loan amount?"
        )
        
        return {
            'messages': [AIMessage(content=reject_msg)],
            'selected_loan': None,  # Clear selection
            'routing_decision': 'waiting_for_user'  # ✅ Ask user to reselect, not automatic routing
        }



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
    

def calculate_amortization_schedule_node(state: Loan_agent_state): 
    print('-----------Calculating Amortisation Schedule-------------')

    loan = state.get('selected_loan')
    if not loan: 
        print('Loan does not exists')
        return {
            "messages": [AIMessage(content="Error: No loan details found.")],
            "routing_decision": "goto_sales_agent"
        }
    print(f"---DEBUG: Loan details - Amount: ₹{loan.amount}, Rate: {loan.interest_rate}%, Tenure: {loan.tenure_years} years---")

    try:    
        schedule_result = calculate_amortization_schedule_tool.invoke({
            'amount': loan.amount,
            'interest_rate': loan.interest_rate,
            'tenure_years': loan.tenure_years
        })
        print(f"---DEBUG: Tool returned type: {type(schedule_result)}---")
        print(f"---DEBUG: Tool returned status: {schedule_result.get('status') if isinstance(schedule_result, dict) else 'NOT A DICT'}---")
        
        if isinstance(schedule_result, dict) and schedule_result.get('status') == 'success':
            print(f"---SUCCESS: Amortization calculated. Monthly EMI: ₹{schedule_result['monthly_payment']}---")
            
            # CRITICAL: Return this to UPDATE the state
            return {
                "amortization_schedule": schedule_result,
                "routing_decision": "goto_sanctioning"
            }
        else:
            print(f"---ERROR: Calculation failed or returned wrong format---")
            return {
                "messages": [AIMessage(content="Error: Could not calculate amortization schedule.")],
                "routing_decision": "goto_sales_agent"
            }
        
    except Exception as e:
        return {'status': 'error', 'detail': str(e)}
    

def loan_query_handler_node(state: Loan_agent_state) -> dict:
    """
    Handles queries about existing loans (amortization, payment details, etc.)
    """
    print("---NODE: LoanQueryHandlerNode---")
    
    last_message = state['messages'][-1].content.lower()
    
    # Check what the user is asking about
    query_keywords = {
        'schedule': ['schedule', 'amortization', 'payment breakdown', 'monthly payment'],
        'summary': ['summary', 'total', 'how much', 'overview'],
        'balance': ['balance', 'remaining', 'left to pay'],
        'interest': ['interest', 'how much interest']
    }
    
    query_type = None
    for qtype, keywords in query_keywords.items():
        if any(keyword in last_message for keyword in keywords):
            query_type = qtype
            break
    
    # Get the amortization data
    schedule_data = state.get('amortization_schedule')
    loan = state.get('selected_loan')
    total_months = loan.tenure_years * 12
    
    if not schedule_data or not loan:
        response = "I don't have loan details available. Please complete your application first."
        return {
            'messages': [AIMessage(content=response)],
            'routing_decision': 'waiting_for_user'
        }
    
    # Generate response based on query type
    if query_type == 'schedule':
        # Show first 6 months of schedule
        schedule_preview = schedule_data['schedule'][:total_months]
        schedule_text = "\n".join([
            f"Month {item['month']}: Payment ₹{item['payment']:,.2f} "
            f"(Principle: ₹{item['principle']:,.2f}, Interest: ₹{item['interest']:,.2f}, "
            f"Balance: ₹{item['balance']:,.2f})"
            for item in schedule_preview
        ])
        
        response = (
            f"Here's your amortization schedule for your loan:\n\n{schedule_text}\n\n"
            f"Monthly Payment: ₹{schedule_data['monthly_payment']:,.2f}\n"
            f"Would you like to see any other details?"
        )
    
    elif query_type == 'summary':
        response = (
            f"**Loan Summary**\n\n"
            f"Principle Amount: ₹{loan.amount:,.2f}\n"
            f"Interest Rate: {loan.interest_rate}% per year\n"
            f"Tenure: {loan.tenure_years} years ({loan.tenure_years * 12} months)\n"
            f"Monthly Payment: ₹{schedule_data['monthly_payment']:,.2f}\n"
            f"Total Amount Payable: ₹{schedule_data['total_payment']:,.2f}\n"
            f"Total Interest: ₹{schedule_data['total_interest']:,.2f}"
        )
    
    elif query_type == 'interest':
        response = (
            f"Your total interest over {loan.tenure_years} years will be "
            f"₹{schedule_data['total_interest']:,.2f}.\n\n"
            f"This is calculated at {loan.interest_rate}% annual interest rate."
        )
    
    else:
        # General query - use LLM with context
        context = (
            f"Loan Amount: ₹{loan.amount:,}, Interest Rate: {loan.interest_rate}%, "
            f"Tenure: {loan.tenure_years} years, Monthly Payment: ₹{schedule_data['monthly_payment']:,.2f}, "
            f"Total Interest: ₹{schedule_data['total_interest']:,.2f}"
        )
        
        prompt = f"""You are a helpful loan advisor. Answer this question about the user's loan:
        
User Question: {state['messages'][-1].content}

Loan Details: {context}

Provide a clear, friendly response."""
        
        response = llm.invoke(prompt).content
    
    return {
        'messages': [AIMessage(content=response)],
        'routing_decision': 'waiting_for_user'
    }


def add_customer_node(state: Loan_agent_state):
    """
    Handles new customer registration.
    Extracts customer details and adds them to the database.
    """
    print("---NODE: AddCustomerNode---")
    
    last_message_obj = state['messages'][-1]
    last_message = last_message_obj.content
    
    # Only process if we're expecting registration details
    if not state.get('awaiting_registration_details'):
        print("Not awaiting registration details. Skipping.")
        return {"routing_decision": "goto_sales_agent"}
    
    # Check if this is a HumanMessage
    if not isinstance(last_message_obj, HumanMessage):
        return {"routing_decision": "goto_sales_agent"}
    
    print(f"Extracting customer details from: {last_message}")
    
    try:
        # Extract customer data using LLM
        user_details = customer_data_llm.invoke(last_message)
        
        print(f"Extracted details: Name={user_details.customer_name}, Phone={user_details.customer_phone}, Address={user_details.customer_address}")
        
        # Add customer to database
        add_result = add_new_customer_tool.invoke({
            'name': user_details.customer_name,
            'phone': user_details.customer_phone,
            'address': user_details.customer_address,
            'credit_score': user_details.credit_score,
            'pre_approved_limit': 50000,
            'pin': user_details.pin
        })
        
        print(f"Add result: {add_result}")
        
        # Check if registration was successful
        if isinstance(add_result, dict) and add_result.get('status') == 'Success':
            customer_id = add_result.get('customer_id')
            
            success_msg = (
                f"✅ Great! I've registered you successfully.\n\n"
                f"**Your Details:**\n"
                f"- Name: {user_details.customer_name}\n"
                f"- Phone: {user_details.customer_phone}\n"
                f"- Customer ID: {customer_id}\n\n"
                f"Now let me fetch your personalized loan options..."
            )
            
            # Mark as verified and proceed to loan options
            return {
                'messages': [AIMessage(content=success_msg)],
                'is_existing': True,  # Now they exist!
                'is_verified': True,
                'customer_id': customer_id,
                'customer_phone': user_details.customer_phone,
                'credit_score': user_details.credit_score,
                'customer_details': {
                    'id': customer_id,
                    'name': user_details.customer_name,
                    'phone': user_details.customer_phone,
                    'credit_score': user_details.credit_score,
                    'pre_approved_limit': 50000
                },
                'awaiting_registration_details': False,
                'routing_decision': 'goto_underwriting'  # Go get loan options!
            }
        else:
            # Registration failed
            error_detail = add_result.get('detail', 'Unknown error')
            
            error_msg = (
                f"❌ Sorry, I couldn't register you: {error_detail}\n\n"
                "Please try again or contact support."
            )
            
            return {
                'messages': [AIMessage(content=error_msg)],
                'awaiting_registration_details': False,
                'routing_decision': 'goto_sales_agent'
            }
    
    except Exception as e:
        print(f"Error in add_customer_node: {e}")
        import traceback
        traceback.print_exc()
        
        error_msg = (
            f"❌ I encountered an error processing your details: {str(e)}\n\n"
            "Could you please provide your information again?\n"
            "Format: Name, Phone, Address, Credit Score, PIN"
        )
        
        return {
            'messages': [AIMessage(content=error_msg)],
            'routing_decision': 'waiting_for_user'
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

def registration_router(state: Loan_agent_state) -> str:
    decision = state.get("routing_decision")
    print(f"---ROUTER (Registration): --> {decision} ---")
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
workflow.add_node("calculate_amortization", calculate_amortization_schedule_node)
workflow.add_node("handle_loan_query", loan_query_handler_node)
workflow.add_node("register_customer", add_customer_node)


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
        "goto_registration": "register_customer",
        "goto_extraction": "extract_choice",
        "goto_income_verification": "verify_uploaded_income",
        "goto_loan_query": "handle_loan_query",
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
        "goto_sanctioning": "calculate_amortization", # Approved!
        "waiting_for_user" : END,
        "goto_sales_agent": "sales_agent"        # Needs upload or is rejected
    }
)

# Router for the VerifyIncomeNode (File Check)
workflow.add_conditional_edges(
    "verify_uploaded_income",
    income_verify_router,
    {
        "goto_sanctioning": "calculate_amortization", # File found, approved!
        "goto_sales_agent": "sales_agent"        # File not found
    }
)

workflow.add_conditional_edges(
    "register_customer",
    registration_router,
    {
        "goto_underwriting": "present_offers",  # Success - get loan options
        "goto_sales_agent": "sales_agent",      # Failure - back to chat
        "waiting_for_user": END                 # Waiting for more info
    }
)

# Simple edges for nodes that have only one possible next step
workflow.add_edge("present_offers", "sales_agent")
workflow.add_edge("generate_sanction", "sales_agent")
workflow.add_edge("calculate_amortization", "generate_sanction")
workflow.add_edge("handle_loan_query", "sales_agent")


conn = sqlite3.connect("memory.db", check_same_thread=False)

# 2. Instantiate the SqliteSaver directly with the connection
memory = SqliteSaver(conn=conn)

# 3. Now, compile the app with the *real* saver object
app = workflow.compile(checkpointer=memory)

# Create a session thread 
config = {'configurable': {'thread_id': 2}}

print("Graph compiled successfully.")

# make a runnable chatbot with while loop

print("Graph compiled successfully.")
print("Chatbot started! Type 'exit' to quit.\n")

"""
# Create a session thread 
config = {'configurable': {'thread_id': 14}}

while True:
    user_input = input('You: ')
    
    if user_input.lower() == 'exit':
        print("Goodbye!")
        break
    
    if not user_input.strip():  # Skip empty inputs
        continue
    
    try:
        # Invoke the graph with the new message
        input_data = {'messages': [HumanMessage(content=user_input)]}
        final_state = app.invoke(input_data, config=config)
        
        # Get the last AI message
        ai_response = final_state['messages'][-1]
        
        # Only print if it's an AI message
        if isinstance(ai_response, AIMessage):
            print(f'\nAssistant: {ai_response.content}\n')
        else:
            print(f'\nAssistant: {ai_response}\n')
            
    except Exception as e:
        print(f"\nError: {e}\n")
        print("Please try again.")


"""
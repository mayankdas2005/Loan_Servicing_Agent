import os
import uvicorn
from fastapi import FastAPI, HTTPException
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pydantic import BaseModel
from psycopg2.extras import Json

# --- 1. Load Environment Variables ---
# Load the .env file (e.g., 'api_secret.env')
load_dotenv("api_secret.env")

# Build the database connection string from .env variables
# This is a secure way to connect without hardcoding passwords.
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "postgres")

if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable is not set!")

encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"



class LoanApplicationLog(BaseModel):
    customer_id: int
    plan_name: str
    amount: int
    interest_rate: float
    tenure_years: int



# --- 2. Create a Connection Pool ---
# This is a production-grade practice. Instead of one connection,
# we create a "pool" of connections. This is much faster and
# more stable for an app that gets many requests.
try:
    psql_pool = SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=DATABASE_URL
    )
    print("Database connection pool created successfully.")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    # Handle the error appropriately, maybe exit
    exit()


# --- 3. Initialize the FastAPI App ---
app = FastAPI(
    title="Tata Capital Mock API Server",
    description="Provides CRM and Loan Option endpoints for the Agentic AI."
)

# --- 4. The "CRM Server" Endpoint ---
@app.get("/crm/verify")
def verify_customer(phone: str):
    """
    This is the mock CRM API endpoint (the "Verification Agent's" tool).
    It searches the database for a customer by their phone number.
    """
    print(f"Received request for /crm/verify with phone: {phone}")
    
    # Define the SQL query
    query = "SELECT * FROM customers WHERE phone = %s"
    
    conn = None
    cursor = None
    try:
        # Get a connection from the pool
        conn = psql_pool.getconn()
        # Use RealDictCursor to get results as dictionaries (like JSON)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(query, (phone,))
        customer_data = cursor.fetchone()
        
        if customer_data:
            print(f"Found customer: {customer_data['name']}")
            return {"status": "Verified", "data": customer_data}
        else:
            print("Customer not found.")
            raise HTTPException(status_code=404, detail="Customer not found")
            
    except Exception as e:
        print(f"Database error in /crm/verify: {e}")
        raise HTTPException(status_code=500, detail="Database internal error")
    finally:
        # Always return the connection to the pool
        if cursor:
            cursor.close()
        if conn:
            psql_pool.putconn(conn)

# --- 5. The "Loan Options" Endpoint ---
@app.get("/loans/options")
def get_loan_options(credit_score: int):
    """
    This is the mock Loan API endpoint (the "Underwriting Agent's" tool).
    It finds loan options based on the customer's credit score.
    """
    print(f"Received request for /loans/options with score: {credit_score}")
    
    # Find all loans where the score is a match
    query = "SELECT * FROM loan_options WHERE %s BETWEEN min_score AND max_score"
    
    conn = None
    cursor = None
    try:
        conn = psql_pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(query, (credit_score,))
        options = cursor.fetchall()
        
        if not options:
            print("No loan options found for this score.")
            return {"status": "No Options Found", "options": []}
        
        print(f"Found {len(options)} loan options.")
        return {"status": "Success", "options": options}

    except Exception as e:
        print(f"Database error in /loans/options: {e}")
        raise HTTPException(status_code=500, detail="Database internal error")
    finally:
        if cursor:
            cursor.close()
        if conn:
            psql_pool.putconn(conn)

@app.post("/applications/log")
def log_application(loan_log: LoanApplicationLog):
    """
    Logs a finalized loan application into the 'applications' table.
    """
    print(f"Received request to log application for customer: {loan_log.customer_id}")
    
    query = """
    INSERT INTO applications (customer_id, plan_name, amount, interest_rate, tenure_years)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING application_id
    """
    
    conn = None
    cursor = None
    try:
        conn = psql_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute(query, (
            loan_log.customer_id,
            loan_log.plan_name,
            loan_log.amount,
            loan_log.interest_rate,
            loan_log.tenure_years
        ))
        
        # Get the new application_id that the database generated
        new_app_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Successfully logged new application with ID: {new_app_id}")
        return {"status": "success", "application_id": new_app_id}
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Database error in /applications/log: {e}")
        raise HTTPException(status_code=500, detail="Database internal error")
    finally:
        if cursor: cursor.close()
        if conn: psql_pool.putconn(conn)

# --- 6. The "Run" Command ---
if __name__ == "__main__":
    print(f"Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
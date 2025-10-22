import sqlite3

# --- 1. Define the Database File ---
# Use the same database file as your customer setup
DB_FILE = "bank.db"

# --- 2. Define the Loan Options Table ---
# We'll include min/max scores so your API can filter by creditworthiness
create_table_sql = """
CREATE TABLE IF NOT EXISTS loan_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT NOT NULL,
    min_score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    tenure_years INTEGER NOT NULL
);
"""

# --- 3. Define 10 Mock Loan Options ---
# (plan_name, min_score, max_score, amount, interest_rate, tenure_years)
mock_loan_data = [
    ('Starter Loan', 600, 649, 10000, 14.5, 2),
    ('Small Project Loan', 600, 699, 15000, 13.0, 3),
    ('Good Credit Plan', 650, 749, 30000, 10.5, 3),
    ('Mid-Level Loan', 700, 799, 50000, 8.5, 4),
    ('Debt Consolidator', 700, 799, 75000, 8.0, 5),
    ('Prime Loan', 750, 849, 100000, 6.5, 5),
    ('Prime Plus', 800, 900, 150000, 5.0, 5),
    ('Elite Loan', 800, 900, 200000, 4.5, 3),
    ('Quick Cash', 600, 900, 5000, 18.0, 1),
    ('Home Renovation', 720, 850, 80000, 7.2, 7)
]

# --- 4. Function to Create and Populate the Table ---
def setup_loan_options_table():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute(create_table_sql)
        print("Table 'loan_options' created successfully (or already exists).")
        
        # Insert the data
        # "INSERT OR IGNORE" will skip any entries that might already exist
        # based on a unique constraint, though we don't have one here.
        # It's safer than a plain INSERT if you run the script twice.
        
        # Let's be safer: only insert if the table is empty
        cursor.execute("SELECT COUNT(*) FROM loan_options")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.executemany("""
                INSERT INTO loan_options 
                (plan_name, min_score, max_score, amount, interest_rate, tenure_years) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, mock_loan_data)
            
            conn.commit()
            print(f"Successfully inserted {len(mock_loan_data)} mock loan options.")
        else:
            print("Table 'loan_options' already contains data. No new data inserted.")
            
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

# --- 5. Run the Setup ---

setup_loan_options_table()
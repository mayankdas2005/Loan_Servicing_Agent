import sqlite3

DB_FILE = "bank.db"

create_table_sql = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    pre_approved_limit INTEGER NOT NULL,
    credit_score INTEGER NOT NULL
);
"""


mock_data = [
    ('Priya Sharma', '9876543210', '123 MG Road, Bangalore', 50000, 780),
    ('Rohan Gupta', '1234567890', '456 Main St, Delhi', 25000, 650),
    ('Amit Singh', '5555544444', '789 Park Ave, Mumbai', 100000, 820),
    ('Sneha Reddy', '8888899999', '101 Jubilee Hills, Hyderabad', 75000, 790),
    ('Vikram Kumar', '7777766666', '202 Anna Salai, Chennai', 30000, 680),
    ('Ananya Bose', '6666655555', '303 Salt Lake, Kolkata', 150000, 850),
    ('David Lee', '9999911111', 'A-14 Koregaon Park, Pune', 40000, 710),
    ('Zara Khan', '3333322222', 'B-7, Sector 18, Noida', 90000, 760),
    ('Karan Malhotra', '2222211111', '505 Linking Road, Mumbai', 120000, 810),
    ('Nisha Patel', '4444455555', 'C-9, CG Road, Ahmedabad', 20000, 620)
]

def setup_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute(create_table_sql)
        cursor.executemany("INSERT INTO customers (name, phone, address, pre_approved_limit, credit_score) VALUES (?, ?, ?, ?, ?)", mock_data)
        
        conn.commit()
        print(f"Successfully inserted {len(mock_data)} mock users.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


setup_database()


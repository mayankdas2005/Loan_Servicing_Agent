
---

```markdown
# 🏦 Tata Capital Loan Servicing Agent

> **An AI-powered financial assistant** that helps customers apply for, verify, and manage personal loans — built with **FastAPI**, **Streamlit**, and **LangGraph**, and powered by **Google’s Gemini API** for natural language intelligence.

---

## 🧭 Overview

The **Loan Servicing Agent** is a multi-component intelligent system that simulates a real-world customer support workflow in the banking domain.

It combines:
- 💬 **Conversational AI** (LangGraph + Gemini)
- ⚡ **FastAPI microservices** (CRM + Loan services)
- 🎨 **Streamlit UI** for customer interaction
- 🗄️ **PostgreSQL (with pgVector)** for scalable loan data and embeddings
- 🧠 **LLM-driven business logic** for decision-making and document generation

This project demonstrates how an AI-driven agent can automate end-to-end financial services — from identity verification to loan sanctioning and query handling.

---

## 🧱 Architecture

```

+-------------------------------------------------------------+
|                     Streamlit Frontend                      |
|            (Interactive chat, file upload, UI)              |
+---------------------------▲---------------------------------+
│
│ REST APIs
▼
+---------------------------+---------------------------------+
|                       FastAPI Backend                       |
|   /crm/verify      → Customer verification                  |
|   /loans/options   → Loan recommendation engine              |
|   /applications/log→ Loan application logging                |
|   /add_customer    → Account creation                        |
+---------------------------▲---------------------------------+
│
│ SQL Queries (via psycopg2)
▼
+-------------------------------------------------------------+
|                 PostgreSQL Database               
|        customers | loan_options | applications2      
+-------------------------------------------------------------+

````

---

## 🧩 Key Features

✅ **Conversational Intelligence** — dynamic dialogue flow with LangGraph  
✅ **Real-Time Loan Processing** — CRM verification, loan selection, sanction letter generation  
✅ **FastAPI microservices** — modular REST architecture  
✅ **pgVector-ready database** — supports future AI retrieval and embedding similarity search  
✅ **Streamlit UI** — human-friendly chat interface with session management  
✅ **Secure Environment Handling** — `.env` variables for API and DB credentials  

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Frontend** | Streamlit | Interactive chat-based UI |
| **Backend** | FastAPI | REST APIs for CRM & Loan services |
| **AI Agent** | LangGraph + Gemini API | Conversational logic & decision-making |
| **Database** | PostgreSQL | Structured data |
| **Environment** | Python 3.11+, `requirements.txt` | Dependency management |
| **ORM/Driver** | psycopg2 | Postgres connection pooling |

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/Loan_Servicing_Agent.git
cd Loan_Servicing_Agent-main
````

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a file named `.env` or `api_secret.env` in your project root:

```bash
# Database credentials
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_NAME=mydb

# Google Gemini API Key
API_KEY=your_gemini_api_key
```

---

## 🚀 Running the Application

### Run the FastAPI Backend

```bash
python server.py
```

> Runs the backend server on **[http://localhost:8000](http://localhost:8000)**

### Run the Streamlit Frontend

```bash
streamlit run ui.py
```

> Opens the UI at **[http://localhost:8501](http://localhost:8501)**

---

## 🧮 Database Initialization

Before running the full system, create and populate your database using the setup scripts:

```bash
python setup_postgres_db.py      # Create 'customers' table
python loan_setup_db.py          # Create 'loan_options' table
python loan_log_setup_db.py      # Create 'applications2' table
```

These scripts automatically connect using credentials from `api_secret.env` and populate the database with mock data.

---

## 🧠 AI Agent Flow

1. **Customer Interaction** — via Streamlit chat
2. **Verification** — backend checks `/crm/verify`
3. **Loan Recommendation** — agent fetches eligible plans from `/loans/options`
4. **Approval & Letter Generation** — generates sanction letter PDF
5. **Loan Queries** — agent answers questions like:

   * “Show me my amortization schedule”
   * “What’s my EMI?”
   * “Summarize my loan details”

---

## 🧾 Example API Endpoints

| Endpoint                       | Method | Description                      |
| ------------------------------ | ------ | -------------------------------- |
| `/crm/verify?phone=&pin=`      | `GET`  | Verifies existing customers      |
| `/loans/options?credit_score=` | `GET`  | Retrieves matching loan plans    |
| `/applications/log`            | `POST` | Logs finalized loan applications |
| `/add_customer`                | `POST` | Registers a new customer         |

---

## 🧰 Example Commands

Rebuild database schema manually:

```bash
python setup_postgres_db.py && python loan_setup_db.py && python loan_log_setup_db.py
```

Start both backend & frontend in separate terminals:

```bash
python server.py
streamlit run ui.py
```

---

## 🔐 Environment & Security Notes

* Never commit `.env` or `api_secret.env` with real credentials.
* Store your `API_KEY` and `DB_PASSWORD` securely (e.g., GitHub Secrets, `.env.local`).
* For production, configure **connection pooling** and **rate limits** in FastAPI.

---

## 🧠 Future Roadmap

* [ ] Integrate **embedding-based retrieval** using pgVector
* [ ] Add **semantic loan recommendations** (vector search)
* [ ] Deploy via **Docker + CI/CD pipeline**
* [ ] Add **LangGraph visualization dashboard**

---

## 🤝 Contributing

We welcome contributions!
If you’d like to improve the agent logic, database models, or add new LLM features:

1. Fork this repo
2. Create a feature branch (`feature/your-improvement`)
3. Commit your changes
4. Open a Pull Request

---

## 🧑‍💻 Maintainers

**Developed by:**
📍 *Mayank Das NIT Trichy*
*
---

## 🌟 Acknowledgements

Special thanks to:

* [LangGraph](https://github.com/langchain-ai/langgraph)
* [Google Gemini](https://deepmind.google/technologies/gemini/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Streamlit](https://streamlit.io/)
* [pgVector](https://github.com/pgvector/pgvector)

> *Built with ❤️ for AI-driven financial innovation.*

```
---



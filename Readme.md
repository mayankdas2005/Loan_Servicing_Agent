
<h1 align="center">🏦 Tata Capital Loan Servicing Agent</h1>

<p align="center">
  <a href="https://fastapi.tiangolo.com/">
    <img alt="Framework" src="https://img.shields.io/badge/Framework-FastAPI-green?logo=fastapi">
  </a>
  <a href="https://www.streamlit.io/">
    <img alt="Frontend" src="https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit">
  </a>
  <a href="https://www.python.org/">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white">
  </a>
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg">
  </a>
</p>

> **An AI-powered financial assistant** that helps customers apply for, verify, and manage personal loans — built with **FastAPI**, **Streamlit**, and **LangGraph**, and powered by **Google’s Gemini API** for natural language intelligence.

---

## 🧭 Overview

The **Loan Servicing Agent** is a multi-component intelligent system that simulates a real-world customer support workflow in the banking domain.

It combines:
- 💬 **Conversational AI** (LangGraph + Gemini)
- ⚡ **FastAPI microservices** (CRM + Loan services)
- 🎨 **Streamlit UI** for customer interaction
- 🗄️ **PostgreSQL** for scalable loan data
- 🧠 **LLM-driven business logic** for decision-making and document generation

This project demonstrates how an AI-driven agent can automate end-to-end financial services — from identity verification to loan sanctioning and query handling.

---

## 🧩 Key Features

* ✅ **Conversational Intelligence** — dynamic dialogue flow with LangGraph
* ✅ **Real-Time Loan Processing** — CRM verification, loan selection, sanction letter generation
* ✅ **FastAPI microservices** — modular REST architecture
* ✅ **Streamlit UI** — human-friendly chat interface with session management
* ✅ **Secure Environment Handling** — `.env` variables for API and DB credentials

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Frontend** | Streamlit | Interactive chat-based UI |
| **Backend** | FastAPI | REST APIs for CRM & Loan services |
| **AI Agent** | LangGraph + Gemini API | Conversational logic & decision-making |
| **Database** | PostgreSQL | Structured data |
| **Environment** | Python 3.11+ | Dependency management |
| **ORM/Driver** | psycopg2 | Postgres connection pooling |

---

## 🛠️ Installation & Setup

Follow these steps to get your environment set up and running.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/Loan_Servicing_Agent.git](https://github.com/yourusername/Loan_Servicing_Agent.git)
    cd Loan_Servicing_Agent
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
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

You will need **two separate terminals** to run the backend and frontend.

**Terminal 1: Run the FastAPI Backend**
```bash
python server.py
```

📍 Backend will be live at http://localhost:8000

**Terminal 2: Run the Streamlit Frontend**
```bash
streamlit run ui.py
```

📍 Frontend will be live at http://localhost:8501

## Database Initialization

Before running the full system, create and populate your database using the setup scripts.
```bash
python setup_postgres_db.py    # Create 'customers' table
python loan_setup_db.py      # Create 'loan_options' table
python loan_log_setup_db.py    # Create 'applications2' table
```
These scripts automatically connect using credentials from api_secret.env and populate the database with mock data.

## 🧠 AI Agent Flow
**1) Customer Interaction** — via Streamlit chat

**2) Verification** — backend checks /crm/verify

**3) Loan Recommendation** — agent fetches eligible plans from /loans/options

**4) Approval & Letter Generation** — generates sanction letter PDF

**5) Loan Queries** — agent answers questions like:
    “Show me my amortization schedule”
    “What’s my EMI?”
    “Summarize my loan details”

## 🔐 Environment & Security Notes
1) Never commit .env or api_secret.env with real credentials.
2) Store your API_KEY and DB_PASSWORD securely (e.g., GitHub Secrets, .env.local).
3) For production, configure connection pooling and rate limits in FastAPI.

## 🧠 Future Roadmap
1) Integrate embedding-based retrieval using pgVector
2) Add semantic loan recommendations (vector search)
3) Deploy via Docker + CI/CD pipeline
4) Add LangGraph visualization dashboard
5) Multi-agent orchestration for customer support & underwriting

## 🤝 Contributing

We welcome contributions! If you’d like to improve the agent logic, database models, or add new LLM features:

   Fork this repo

   Create a feature branch (feature/your-improvement)

   Commit your changes

   Open a Pull Request

## 🧑‍💻 Maintainers

   Developed by: Mayank Das

## 🪪 License

This project is released under the MIT License. See LICENSE file for details.

## 🌟 Acknowledgements

Special thanks to:

   LangGraph

   Google Gemini

   FastAPI

   Streamlit

   pgVector


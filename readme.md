================================================================
BANK EMAIL AUTOMATION SYSTEM
Complete Project Documentation
================================================================

An AI-powered system that reads customer emails for a bank, understands what the customer wants, fetches information from core banking APIs, drafts a response, and routes it to a human for approval before sending.

Built with Python, FastAPI, LangChain, LangGraph, Ollama (Llama 3), and Streamlit.

----------------------------------------------------------------
TABLE OF CONTENTS
----------------------------------------------------------------

1. Overview
2. Architecture
3. Project Structure
4. How to Run — Setup
5. How to Run — Running the System
6. Running Individual Agents (Optional)
7. Running with Docker (Alternative)
8. What You Should See End to End
9. Checking Logs
10. Stopping Everything
11. Common Issues
12. Business Scenarios Covered
13. Agents
14. MCP Integration
15. Mock Core Banking APIs
16. Security
17. Logging and Audit
18. Human-in-the-Loop
19. Scheduler
20. Error Handling
21. Testing
22. Docker
23. Assumptions
24. Limitations
25. Tech Stack
26. Notes


================================================================
1. OVERVIEW
================================================================

A customer sends an email to the bank asking for something — a balance, recent card transactions, a statement, or a combination of these. The system:

1. Reads and cleans the email body.
2. Detects what the customer wants (intent) and how they are feeling (sentiment).
3. Extracts account numbers, card numbers, dates, and other details.
4. Validates the extracted data through mock core banking APIs.
5. Fetches the required information.
6. Drafts a professional response email.
7. Sends the draft to a human reviewer for approval.
8. Sends the email after approval.

If any part of the request fails — for example, the account is valid but the card is not — the system still completes the valid parts and asks the customer to recheck the invalid ones. This is handled without failing the whole email.


================================================================
2. ARCHITECTURE
================================================================

Incoming Email
      |
Email Reader Module
      |
LLM / NLP Processing (Llama 3)
      |
Intent Detection + Sentiment Analysis
      |
Entity Extraction
      |
Agent Orchestrator (LangGraph)
      |
API Decision Engine
      |
Mock Core Banking APIs (FastAPI)
      |
Response Generator
      |
Human-in-the-Loop (Streamlit)
      |
Final Email Response

The workflow matches the high-level architecture given in the task. Each stage is implemented as a separate agent so that components can be changed or extended without touching the rest of the pipeline.


================================================================
3. PROJECT STRUCTURE
================================================================

bank_email_automation/
├── agents/           AI agents (intent, sentiment, entity, validation, response)
├── apis/             Mock core banking APIs (FastAPI)
├── models/           Pydantic schemas and LLM loader
├── prompts/          Prompt templates for the LLM
├── workflows/        LangGraph orchestrator
├── utils/            Helpers (logging, masking, API client, email sender, attachments)
├── tests/            Test scripts for each agent
├── config/           Configuration files
├── docs/             Architecture, LLD, API spec, assumptions
├── ui/               Streamlit approval dashboard
├── logs/             Audit trail, alerts, sent email records
├── main.py           Scheduler entry point
├── requirements.txt
└── README.md


================================================================
4. HOW TO RUN — SETUP
================================================================

Prerequisites
-------------

1. Python 3.11 or newer
   Check by opening PowerShell and running:
   python --version

   If Python is not installed, download it from https://www.python.org/downloads/ and make sure to tick "Add Python to PATH" during installation.

2. Ollama (for running Llama 3 locally)
   Download from https://ollama.com/download and run the installer.
   After installation, verify with:
   ollama --version

3. Llama 3 model (one-time download, around 4.7 GB)
   ollama pull llama3

   This downloads the model into Ollama's local cache. It only needs to be done once.

4. Verify Ollama is running
   Open a new PowerShell window and run:
   curl http://localhost:11434

   You should see: Ollama is running

   If you do not see this, open the Ollama app from the Start menu and wait a few seconds. It runs a background service on port 11434.


================================================================
HOW TO RUN
================================================================

The system has three components that need to run in parallel.
Each must be started in its own terminal window.

----------------------------------------------------------------
STEP 1: Open Terminal 1 — Start Mock Banking APIs
----------------------------------------------------------------

Open a new PowerShell window and run:

    cd C:\Users\admin\Desktop\bank_email_automation
    venv\Scripts\activate
    python -m apis.main

You should see:

    [START] Mock Banking API server
            Docs: http://localhost:8000/docs
    INFO:     Uvicorn running on http://0.0.0.0:8000

Leave this terminal running. Do not close it.

To verify, open a browser and go to:
    http://localhost:8000/health

You should see:
    {"status":"UP","service":"Mock Core Banking API","timestamp":"..."}

----------------------------------------------------------------
STEP 2: Open Terminal 2 — Start Human-in-the-Loop UI
----------------------------------------------------------------

Open a SECOND PowerShell window (do not close Terminal 1) and run:

    cd C:\Users\admin\Desktop\bank_email_automation
    venv\Scripts\activate
    streamlit run ui/approval_app.py

Streamlit will print a local URL. Open it in a browser:

    http://localhost:8501

You will see the approval dashboard.

Leave this terminal running.

----------------------------------------------------------------
STEP 3 (Optional): Open Terminal 3 — Start Scheduler
----------------------------------------------------------------

Open a THIRD PowerShell window and run:

    cd C:\Users\admin\Desktop\bank_email_automation
    venv\Scripts\activate
    python main.py

This runs the email processing workflow every 10 minutes.
The first run happens immediately for demo purposes.

Leave this terminal running. Press Ctrl+C to stop.

----------------------------------------------------------------
IMPORTANT NOTES
----------------------------------------------------------------

- Ollama must be running in the background before starting any of
  the above. If not, open the Ollama app from the Start menu and
  wait a few seconds. Verify with: curl http://localhost:11434

- Terminal 1 (APIs) must be running before you click "Process Email"
  in the Streamlit UI. Otherwise the agents will fail to fetch data.

- Do not close Terminal 1 or Terminal 2 while testing.

- To stop any component, press Ctrl+C in its terminal window.

----------------------------------------------------------------
WHAT TO DO NEXT
----------------------------------------------------------------

Once Terminal 1 and Terminal 2 are running:

1. Open http://localhost:8501 in your browser.
2. In the left sidebar, click a sample button (for example,
   "Scenario 1 - Balance") or paste your own customer email.
3. Click "Process Email".
4. Wait 30 to 90 seconds for the AI agents to process.
5. Review the generated response and click "Approve & Send".

The approved email will be logged in logs/sent_emails.log.


Setup (First Time Only)
-----------------------

Step 1: Copy the project to your Desktop
   C:\Users\<your-name>\Desktop\bank_email_automation

Step 2: Open PowerShell in the project folder
   cd C:\Users\admin\Desktop\bank_email_automation

Step 3: Create a virtual environment
   python -m venv venv

Step 4: Activate the virtual environment
   venv\Scripts\activate

   After this, the prompt should start with (venv). Example:
   (venv) PS C:\Users\admin\Desktop\bank_email_automation>

Step 5: Install dependencies
   pip install -r requirements.txt

   This installs FastAPI, LangChain, LangGraph, Streamlit, structlog, and the other packages listed in requirements.txt. It may take three to five minutes.

Step 6: Verify the configuration
   python config\config_loader.py

   You should see output similar to:

   [OK] Config loaded successfully
        App Name : Bank Email Automation System
        LLM      : llama3 @ http://localhost:11434
        API Base : http://localhost:8000
        Schedule : every 10 min

   If this works, the environment is ready.


================================================================
5. HOW TO RUN — RUNNING THE SYSTEM
================================================================

The system has three components that run in parallel:

1. Mock Core Banking APIs (FastAPI)
2. Human-in-the-Loop dashboard (Streamlit)
3. Scheduler (Python script that processes emails every 10 minutes)

Each runs in its own terminal window. Below are the exact commands.


Terminal 1 — Mock Core Banking APIs
-----------------------------------

Open a new PowerShell window and run:

   cd C:\Users\admin\Desktop\bank_email_automation
   venv\Scripts\activate
   python -m apis.main

You should see:

   [START] Mock Banking API server
           Docs: http://localhost:8000/docs
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

Leave this terminal running. This server exposes the five banking endpoints that the agents call.

To check that it is up, open a browser and go to http://localhost:8000/health. You should see:

   {"status":"UP","service":"Mock Core Banking API","timestamp":"..."}

You can also open http://localhost:8000/docs to see the interactive Swagger UI and try out each endpoint manually.


Terminal 2 — Human-in-the-Loop UI
---------------------------------

Open a second PowerShell window:

   cd C:\Users\admin\Desktop\bank_email_automation
   venv\Scripts\activate
   streamlit run ui/approval_app.py

Streamlit will print a local URL. Open it in a browser:

   http://localhost:8501

You will see the approval dashboard. The left sidebar lets you paste a customer email or click a sample to auto-fill it. Clicking "Process Email" runs the full pipeline and shows the generated response for approval.

Leave this terminal running.


Terminal 3 — Scheduler
----------------------

Open a third PowerShell window:

   cd C:\Users\admin\Desktop\bank_email_automation
   venv\Scripts\activate
   python main.py

This starts the scheduler. It runs the email processing workflow every 10 minutes. The first run happens immediately so you can see output without waiting.

You will see log lines in the terminal such as:

   {"interval_minutes": 10, "event": "scheduler_starting", ...}
   [DEMO] Running first job immediately...
   [PROCESSED] auto-20261014104401-1: SUCCESS

Leave this terminal running. Press Ctrl+C to stop.


================================================================
6. RUNNING INDIVIDUAL AGENTS (OPTIONAL)
================================================================

Each agent has its own test script. These are useful for debugging or for demonstrating a single part of the pipeline without running the full workflow.

   python -m tests.test_agent_1               # Email understanding
   python -m tests.test_agent_2               # Intent classification
   python -m tests.test_agent_3               # Sentiment analysis
   python -m tests.test_agent_4               # Entity extraction
   python -m tests.test_agent_5               # Validation and API calls
   python -m tests.test_agent_6               # Full pipeline with response
   python -m tests.test_agent_api_selection   # API selection planning

Important: For test_agent_5 and test_agent_6, the mock API server must be running in Terminal 1.

================================================================
LLM MODEL USED
================================================================

This system uses Llama 3 (8B parameters) as the primary language model.

Model: Llama 3 (8B)
Provider: Meta
Host: Ollama (local inference on port 11434)
Framework: LangChain (langchain_community.llms.Ollama)
Temperature: 0.2
Max Tokens: 1024

The model runs locally on the machine, so customer email data never leaves
the bank's infrastructure. This is important for compliance and data privacy.

Agents that use the LLM:

- Email Understanding Agent (summarization)
- Intent Classification Agent (intent detection)
- Sentiment Analysis Agent (sentiment detection)
- Entity Extraction Agent (entity extraction)
- Response Generation Agent (drafting responses)

Agents that do not use the LLM (deterministic logic):

- API Selection Agent (rule-based mapping)
- Validation Agent (API calls and validation)
- Audit Logging Agent (logging)

A smaller and faster alternative model is available for demo purposes.
To switch, run:

    ollama pull llama3.2:1b

Then change llm.model in config/config.yaml to llama3.2:1b.

The 8B model is more accurate but slower on CPU. The 1B model is faster
but slightly less accurate. In a production setup with GPU inference,
the 8B model would be the default choice.

================================================================
7. RUNNING WITH DOCKER (ALTERNATIVE)
================================================================

If Docker Desktop is installed, the entire stack can be started with a single command.

Step 1: Build the image
   docker build -t bank_email_automation .

Step 2: Start all services
   docker-compose up

This starts four containers:

   bank_api        — Mock banking APIs on port 8000
   bank_ui         — Streamlit dashboard on port 8501
   bank_scheduler  — Scheduler
   bank_ollama     — Ollama for Llama 3

Once started:

   Swagger UI: http://localhost:8000/docs
   Approval dashboard: http://localhost:8501

Step 3: Stop
   Press Ctrl+C in the docker-compose terminal, or run:
   docker-compose down

Note: The first time you run docker-compose, it will need to pull the Ollama image and the Llama 3 model, which can take 15 to 30 minutes depending on internet speed.


================================================================
8. WHAT YOU SHOULD SEE END TO END
================================================================

When everything is running, here is what a full demonstration looks like:

1. Open http://localhost:8501 in a browser.
2. In the sidebar, click the "Scenario 1 — Balance" button to auto-fill a sample email, or paste your own.
3. Click "Process Email".
4. Wait 30 to 90 seconds. The pipeline runs through all agents sequentially.
5. The main panel shows:
   - The original email.
   - The AI summary, intent, sentiment, and extracted entities.
   - The generated response.
   - The audit trail of every agent decision.
6. Click "Approve & Send". The email is sent (in mock mode) and moves to the "Approved & Sent" tab.
7. Check logs/sent_emails.log to confirm the record.


================================================================
9. CHECKING LOGS
================================================================

While the system runs, logs are written to the logs/ folder.

   File                    What it contains
   ----                    ----------------
   logs/audit.log          Every agent decision, in JSON lines
   logs/app.log            Application events
   logs/alerts.log         Warnings and failures
   logs/sent_emails.log    Every email that was approved and sent

To view the last few lines of any log file:

   Get-Content logs\audit.log -Tail 10


================================================================
10. STOPPING EVERYTHING
================================================================

In each terminal window, press Ctrl+C to stop the process.

To deactivate the virtual environment in any terminal:

   deactivate


================================================================
11. COMMON ISSUES
================================================================

Issue: "ollama is not recognized"
Fix: Close all PowerShell windows, open a new one, and try again. If the issue persists, add Ollama to PATH manually:

   $ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama"
   [Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$ollamaPath", "User")

Then open a new PowerShell.


Issue: "Cannot connect to Ollama" when running an agent
Fix: The Ollama background service is not running. Open the Ollama app from the Start menu and wait a few seconds. Verify with:
   curl http://localhost:11434


Issue: "Port 8000 already in use"
Fix: Another process is using port 8000. Either stop that process or change the port in config/config.yaml and in the commands above.


Issue: LLM responses are very slow
Fix: Llama 3 on CPU takes 5 to 30 seconds per agent. The full pipeline can take 30 to 120 seconds per email. This is expected. To speed it up:
   - Use a GPU if available.
   - Or switch to a smaller model: ollama pull llama3.2:1b, then change llm.model in config/config.yaml to llama3.2:1b.


Issue: "ModuleNotFoundError: No module named 'config'"
Fix: The virtual environment is either not active or the config folder is missing. Make sure you are in the project root and that venv\Scripts\activate was run.


================================================================
12. BUSINESS SCENARIOS COVERED
================================================================

The system handles the five scenarios described in the task:

1. Account balance enquiry — customer asks for account balance.
2. Credit card usage enquiry — customer asks for recent card transactions.
3. Statement request — customer asks for a statement for a specific period.
4. Multiple requests in one email — customer asks for more than one thing at once.
5. Partial validation failure — one request succeeds, another fails (for example, account valid, card invalid).

Each scenario has been tested end to end.


================================================================
13. AGENTS
================================================================

The pipeline is split into small agents. Each one has a single responsibility.

   Agent                          Responsibility
   -----                          --------------
   Email Understanding Agent      Summarizes the customer email
   Intent Classification Agent    Detects one or more intents
   Sentiment Analysis Agent       Detects the tone (neutral, positive, negative, urgent)
   Entity Extraction Agent        Pulls account numbers, card numbers, dates, counts
   API Selection Agent            Decides which APIs to call and in what order
   Validation Agent               Validates data and fetches required information
   Response Generation Agent      Drafts the final email response
   Audit Logging Agent            Writes every decision to the audit trail

All agents share a single AgentState object that flows through the LangGraph orchestrator.


================================================================
14. MCP INTEGRATION
================================================================

The banking operations are exposed as MCP-style tools with JSON schemas:

   Tool                     Purpose
   ----                     -------
   validate_account         Check if an account number exists and is active
   validate_card            Check if a card number exists and is active
   get_account_balance      Fetch the current account balance
   get_card_transactions    Fetch recent credit card transactions
   get_statement            Fetch a statement for a given period

Tools are discoverable via MCPServer.discover() and callable via MCPServer.invoke(name, args).

A small bridge in utils/mcp_langchain_tools.py converts these to LangChain StructuredTool objects so agents can use them directly.


================================================================
15. MOCK CORE BANKING APIs
================================================================

Five endpoints are exposed via FastAPI:

   Endpoint                        Purpose
   --------                        -------
   POST /api/v1/validate/account   Validate an account number
   POST /api/v1/validate/card      Validate a card number
   POST /api/v1/account/balance    Fetch account balance
   POST /api/v1/card/transactions  Fetch card transactions
   POST /api/v1/statement          Fetch an account statement

All APIs mask account and card numbers in their responses. Raw numbers never leave the system in a response or a log.


================================================================
16. SECURITY
================================================================

Data masking
   Account numbers, card numbers, email addresses, and phone numbers are masked everywhere they appear (API responses, logs, generated emails). Masking is applied through utils/masking.py.

File safety
   Attachments go through five checks before being saved — extension whitelist, MIME type verification, size limit, malware signature scan, and path traversal sanitization. Implemented in utils/attachment_handler.py.

Local LLM
   Llama 3 runs locally through Ollama. Customer data is not sent to any external service.


================================================================
17. LOGGING AND AUDIT
================================================================

Every decision made by an agent is logged in two places:

   logs/audit.log — one JSON line per agent decision (who, what, input, output, status, latency).
   logs/app.log   — structured application events.

Failures and warnings are also written to logs/alerts.log through the alert manager.

Sent emails are recorded in logs/sent_emails.log.


================================================================
18. HUMAN-IN-THE-LOOP
================================================================

The Streamlit dashboard in ui/approval_app.py lets a human reviewer:

   - Paste a customer email (or click a sample to auto-fill).
   - Process it through the pipeline.
   - See the AI-detected intent, sentiment, entities, and the generated response.
   - Edit the response if needed.
   - Approve and send, or reject.

Only approved emails are sent. Sending is currently in mock mode, which records the email in logs/sent_emails.log instead of using a real SMTP server. Switching to real SMTP is a matter of setting mock=False in utils/email_sender.py.


================================================================
19. SCHEDULER
================================================================

main.py runs the workflow every 10 minutes using APScheduler. It fetches new emails, processes each one, and hands the result off to the approval queue. The first run happens immediately for demo purposes.


================================================================
20. ERROR HANDLING
================================================================

- API timeouts and connection failures are retried once by the API client.
- Invalid account or card numbers do not crash the pipeline. The validation agent records the failure and continues with whatever succeeded.
- LLM JSON parsing is retried up to two times with an additional instruction if the first response is not valid JSON.
- The orchestrator wraps the pipeline in a try/except block and raises an alert on unexpected failures.


================================================================
21. TESTING
================================================================

Each agent has a test script under tests/:

   python -m tests.test_agent_1               # Email understanding
   python -m tests.test_agent_2               # Intent classification
   python -m tests.test_agent_3               # Sentiment analysis
   python -m tests.test_agent_4               # Entity extraction
   python -m tests.test_agent_5               # Validation and API calls
   python -m tests.test_agent_6               # Full pipeline with response
   python -m tests.test_agent_api_selection   # API selection planning

All tests were run locally on Llama 3 and pass.


================================================================
22. DOCKER
================================================================

A Dockerfile and docker-compose.yml are included.

   docker-compose up --build

This starts four services: the mock APIs, the Streamlit UI, the scheduler, and Ollama.

The image can be built with:

   docker build -t bank_email_automation .


================================================================
23. ASSUMPTIONS
================================================================

- Core banking APIs are mocked. No real banking data is used.
- The email server is simulated. IMAP fetch is a placeholder for production.
- Authentication is simplified for this proof of concept.
- Llama 3 runs on CPU in the development environment. Response times per email are in the range of 30 to 120 seconds. A GPU or a smaller model would reduce this significantly.


================================================================
24. LIMITATIONS
================================================================

- No persistent database. State is held in memory, and logs are written to disk.
- The scheduler processes emails sequentially. Parallel processing would improve throughput at higher volumes.
- Sending is in mock mode by default.
- Attachment handling supports PDF, PNG, and JPG files. OCR depends on the Tesseract binary being installed on the system.


================================================================
25. TECH STACK
================================================================

   Component            Technology
   ---------            ----------
   Language             Python
   LLM                  Llama 3 via Ollama
   Agent Framework      LangGraph, LangChain
   API Framework        FastAPI, Uvicorn
   Data Validation      Pydantic v2
   Scheduling           APScheduler
   Logging              structlog
   UI                   Streamlit
   Deployment           Docker


================================================================
26. NOTES
================================================================

This project was built as part of an interview assignment for an Intelligent Email Processing System. The goal was to design and implement a working pipeline that covers the functional requirements, handles the five business scenarios, and demonstrates how a production system of this kind could be structured.

The code is modular. Adding a new intent only requires a new prompt and a new entry in the intent enum, without changing the core pipeline.


================================================================
END OF DOCUMENT
================================================================
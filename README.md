# ✈️ Flight Deals Agent as a Service (AaaS)

An AI-powered global flight search assistant that finds the best real-time deals using natural language. Now with multi-model support and a specialized Guardrail Agent for verification.

---

## 🌟 Features

- **Natural Language Search**: Ask for flights like you're talking to a travel agent.
- **Real-Time Data**: Integrated with the **SerpApi Google Flights engine** for live pricing, duration, and carbon emissions.
- **Multi-Model Support**: Choose your preferred AI provider:
  - **Google Gemini** (1.5 Flash)
  - **Perplexity** (Sonar)
  - **OpenAI** (GPT-4o-mini)
  - **Anthropic** (Claude 3.5 Sonnet)
- **Guardrail Agent**: Every search is verified by a second "Supervisor" agent to ensure accuracy and prevent hallucinations.
- **Session-Based API Keys**: Securely enter your own API keys in the UI (they are not stored on the server).
- **Responsive UI**: Built with Streamlit, featuring rich result cards and quick-route buttons.

---

## 🏗️ Architecture

The project follows a modular "Agent-as-a-Service" pattern:

1.  **Backend (FastAPI)**:
    - Exposes a `/ask` REST endpoint.
    - Orchestrates the LLM factory and agent execution.
2.  **AI Agent (LangChain)**:
    - **Flight Agent**: Processes natural language to extract origin/destination and calls tools.
    - **Verifier Agent**: Reviews the Flight Agent's output against the user's original request to ensure high fidelity.
3.  **Search Tool**:
    - Direct integration with Google Flights data via SerpApi.
4.  **Frontend (Streamlit)**:
    - Interactive chat interface with a dedicated "Model Settings" sidebar.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- [SerpApi Key](https://serpapi.com/) (Required for flight data)
- API Key for your preferred LLM provider (Google, Perplexity, OpenAI, or Anthropic)

### 2. Installation
```bash
git clone https://github.com/jayshilj/flight-deals-aaas.git
cd flight-deals-aaas
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
SERPAPI_API_KEY=your_serpapi_key_here
GOOGLE_API_KEY=your_google_key_here  # Optional if providing in UI
```

### 4. Running the App
Start the **FastAPI Backend** first:
```bash
python -m uvicorn app.main:app --reload
```

Then, in a new terminal, start the **Streamlit Frontend**:
```bash
streamlit run app/ui.py
```

---

## 💡 Example Queries
- *"Cheapest flights from Austin to LA on April 15"*
- *"Round trip AUS to NYC April 20, return April 27"*
- *"Flights from Dallas to Miami on 2026-05-01"*

---

## 🛠️ Technology Stack
- **Frameworks**: FastAPI, Streamlit
- **AI Orchestration**: LangChain, LangChain-Classic
- **Models**: Google Gemini, Perplexity Sonar, OpenAI GPT, Anthropic Claude
- **Data Source**: SerpApi (Google Flights)
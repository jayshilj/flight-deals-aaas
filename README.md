# 🌍 Complete Trip Agent as a Service (AaaS)

An AI-powered global travel assistant that plans your entire trip using natural language. Upgraded with a **Multi-Agent Architecture**, it seamlessly orchestrates Flight, Hotel, and Activity searches, all verified by a rigorous Guardrail Agent with an active Rework Feedback Loop.

---

## 🌟 Features

- **Complete Trip Planning**: Ask for flights, hotels, and itineraries all in one prompt.
- **Multi-Agent Orchestration**: A Trip Orchestrator delegates tasks to specialized sub-agents:
  - ✈️ **Flight Agent**: Real-time Google Flights data via SerpApi.
  - 🏨 **Hotel Agent**: Real-time Google Hotels data via SerpApi.
  - 📍 **Activity Agent**: Google Local/Web Search data for attractions and itineraries.
- **Guardrail Rework Loop**: A stringent Verifier Agent reviews all outputs. If it detects poor hotel ratings or generic "tourist trap" itineraries, it issues a `REWORK` command, forcing the sub-agents to retry and improve the results.
- **Multi-Model Support**: Choose your preferred AI provider:
  - **Google Gemini** (2.5 Flash)
  - **Perplexity** (Sonar)
  - **OpenAI** (GPT-4o-mini)
  - **Anthropic** (Claude 3.5 Sonnet)
- **Transparent Execution**: Expandable UI sections to view exact **Agent Data Citations & Tools** (grouped by attempt) and **Guardrail Verifier Checks**.
- **Responsive Modern UI**: Built with Streamlit, featuring a glassmorphism design and Markdown tables for clear, beautiful results.

---

## 🏗️ Architecture

The project follows a robust "Supervisor Multi-Agent" pattern:

1.  **Trip Orchestrator**: Analyzes the request and builds a JSON execution plan.
2.  **Sub-Agents (LangChain)**: Run parallel/sequential tool calls to gather real-time travel data.
3.  **Guardrail Verifier**: Checks the aggregated data against quality standards. If it fails, it triggers a feedback loop back to the sub-agents.
4.  **FastAPI Backend**: Exposes a `/ask` REST endpoint orchestrating the LLM factory.
5.  **Streamlit Frontend**: Displays the fully verified trip package and the interactive agent logs.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- [SerpApi Key](https://serpapi.com/) (Required for Google Flights, Hotels, and Local searches)
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
- *"Find me a flight to Denver next Friday, a 4-star hotel, and a 2-day hiking itinerary."*
- *"Cheapest flights from Austin to LA on April 15 with a budget hotel."*
- *"Find me a trip to a tourist trap in Denver with the worst-rated hotels."* (Watch the Guardrail trigger a rework!)

---

## 🛠️ Technology Stack
- **Frameworks**: FastAPI, Streamlit
- **AI Orchestration**: LangChain, Multi-Agent Feedback Loops
- **Models**: Google Gemini, Perplexity Sonar, OpenAI GPT, Anthropic Claude
- **Data Source**: SerpApi (Google Flights, Hotels, Local Search)
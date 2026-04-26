import streamlit as st
import requests

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="✈ Flight Deals Agent",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Light Theme CSS ───────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }

    .header-box {
        background: linear-gradient(120deg, #0066FF, #00AAFF);
        border-radius: 16px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 24px;
    }
    .header-box h1 { color: white; margin: 0; font-size: 2rem; }
    .header-box p  { color: rgba(255,255,255,0.85); margin: 6px 0 0 0; }

    .flight-card {
        background: #ffffff;
        border: 1.5 solid #e0e8ff;
        border-radius: 14px;
        padding: 18px 22px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,102,255,0.07);
    }
    .best-card {
        background: #f0f7ff;
        border: 2px solid #0066FF;
        border-radius: 14px;
        padding: 18px 22px;
        margin: 10px 0;
        box-shadow: 0 4px 16px rgba(0,102,255,0.12);
    }
    .price { font-size: 1.8rem; font-weight: 800; color: #0066FF; }
    .airline { font-size: 1.05rem; font-weight: 600; color: #1a1a2e; }
    .detail { color: #555; font-size: 0.9rem; margin-top: 4px; }
    .badge-best {
        background: #0066FF; color: white;
        border-radius: 6px; padding: 3px 10px;
        font-size: 0.75rem; font-weight: 700;
    }
    .badge-nonstop {
        background: #e6fff0; color: #00aa55;
        border: 1px solid #00aa55;
        border-radius: 6px; padding: 2px 8px;
        font-size: 0.78rem; font-weight: 600;
    }
    .tip-box {
        background: #f0f4ff;
        border-left: 4px solid #0066FF;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.9rem;
        color: #333;
    }
    div[data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈ Flight Deals Agent")
    st.caption("AI-Powered Global Flight Search")
    st.divider()

    # --- Model Settings ---
    st.markdown("### ⚙️ Model Settings")
    provider = st.selectbox(
        "Select Provider",
        ["Google", "Perplexity", "OpenAI", "Anthropic"],
        index=0
    )
    
    # Default models for each provider
    default_models = {
        "Google": "gemini-1.5-flash",
        "Perplexity": "sonar",
        "OpenAI": "gpt-4o-mini",
        "Anthropic": "claude-3-5-sonnet-latest"
    }
    
    model_name = st.text_input("Model Name", value=default_models.get(provider, ""))
    user_api_key = st.text_input(f"{provider} API Key", type="password", placeholder=f"Enter {provider} API Key...")
    
    if not user_api_key:
        st.info(f"💡 Using server {provider} key if set.")
    
    st.divider()

    st.markdown("### 💡 Try These Queries")
    st.markdown("""
<div class='tip-box'>
• "Cheapest flights from Austin to LA on April 15"<br><br>
• "Round trip AUS to NYC April 20, return April 27"<br><br>
• "Flights from Dallas to Miami on 2026-05-01"
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🚀 Quick Routes from Austin")
    quick_routes = {
        "✈ AUS → LAX (Los Angeles)": "Cheapest flights from Austin to Los Angeles on 2026-04-15",
        "✈ AUS → ORD (Chicago)":     "Cheapest flights from Austin to Chicago on 2026-04-15",
        "✈ AUS → JFK (New York)":    "Cheapest flights from Austin to New York on 2026-04-15",
        "✈ AUS → MIA (Miami)":       "Cheapest flights from Austin to Miami on 2026-04-15",
        "✈ AUS → SFO (San Francisco)": "Cheapest flights from Austin to San Francisco on 2026-04-15",
    }
    for label, query in quick_routes.items():
        if st.button(label, use_container_width=True, key=label):
            st.session_state.quick_query = query

    st.divider()
    st.caption("🔒 API keys entered here are NOT stored.")

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class='header-box'>
    <h1>✈ Flight Deals Agent</h1>
    <p>Ask me to find the best flights — now with Guardrail Agent verification</p>
</div>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hi! I'm your **Flight Deals Agent**. I search real Google Flights data to find you the best prices!\n\n**Try asking:** *\"Find cheapest flights from Austin to Los Angeles on 2026-04-20\"*"
    })

# ── Chat History ──────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "✈"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── API Call Helper ───────────────────────────────────────────
def call_agent(query: str, provider: str, model_name: str, api_key: str) -> str:
    try:
        payload = {
            "query": query,
            "provider": provider,
            "model_name": model_name,
            "api_key": api_key if api_key else None
        }
        resp = requests.post(
            "http://127.0.0.1:8000/ask",
            json=payload,
            timeout=120 # Increased timeout for dual-agent processing
        )
        resp.raise_for_status()
        data = resp.json()

        if "response" in data and data["response"]:
            return data["response"]
        elif "detail" in data:
            return f"❌ Server error: {data['detail']}"
        else:
            return f"⚠️ Unexpected response format: {str(data)}"

    except requests.exceptions.ConnectionError:
        return (
            "❌ **Cannot connect to the Flight Agent API.**\n\n"
            "Make sure FastAPI is running in your first terminal:\n"
            "```\nuvicorn app.main:app --reload\n```"
        )
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The agents are taking too long — try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ── Handle Queries ────────────────────────────────────────────
def process_query(q: str):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(q)
    with st.chat_message("assistant", avatar="✈"):
        with st.spinner(f"🔍 Searching via {provider} ({model_name})..."):
            result = call_agent(q, provider, model_name, user_api_key)
        st.markdown(result)
    st.session_state.messages.append({"role": "assistant", "content": result})

# Quick routes
if "quick_query" in st.session_state:
    query = st.session_state.pop("quick_query")
    process_query(query)
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about flights... e.g. 'Cheapest AUS to LAX on 2026-04-20'"):
    process_query(prompt)
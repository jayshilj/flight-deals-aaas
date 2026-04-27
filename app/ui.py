import streamlit as st
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="✈ Flight Deals Agent",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Light Theme CSS ───────────────────────────────────────────
# Formatted to improve readability
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stApp { background-color: #f7f9fc; }

    .header-box {
        background: linear-gradient(135deg, #0066FF 0%, #00d2ff 100%);
        border-radius: 24px;
        padding: 32px 40px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 102, 255, 0.25);
    }
    .header-box h1 { color: white; margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; }
    .header-box p  { color: rgba(255,255,255,0.95); margin: 8px 0 0 0; font-size: 1.1rem; font-weight: 500;}

    .flight-card {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 12px 0;
        box-shadow: 0 4px 16px rgba(0,102,255,0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .flight-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,102,255,0.12);
    }
    .best-card {
        background: linear-gradient(145deg, #ffffff 0%, #f0f7ff 100%);
        border: 2px solid #0066FF;
        border-radius: 16px;
        padding: 20px 24px;
        margin: 12px 0;
        box-shadow: 0 8px 24px rgba(0,102,255,0.15);
    }
    .price { font-size: 2rem; font-weight: 800; color: #0066FF; letter-spacing: -0.5px;}
    .airline { font-size: 1.1rem; font-weight: 700; color: #1a1a2e; }
    .detail { color: #555; font-size: 0.95rem; margin-top: 6px; font-weight: 500;}
    .badge-best {
        background: linear-gradient(90deg, #0066FF, #00aaff); color: white;
        border-radius: 8px; padding: 4px 12px;
        font-size: 0.8rem; font-weight: 700;
        box-shadow: 0 2px 8px rgba(0,102,255,0.3);
    }
    .badge-nonstop {
        background: #e6fff0; color: #00aa55;
        border: 1px solid #00aa55;
        border-radius: 8px; padding: 3px 10px;
        font-size: 0.8rem; font-weight: 600;
    }
    .tip-box {
        background: rgba(240, 244, 255, 0.7);
        border-left: 4px solid #0066FF;
        border-radius: 12px;
        padding: 16px 20px;
        font-size: 0.95rem;
        color: #333;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    div[data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 12px;
        background: rgba(255,255,255,0.6);
        border: 1px solid rgba(255,255,255,0.8);
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
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
        "Google": "gemini-2.5-flash",
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
    
    target_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    quick_routes = {
        "✈ AUS → LAX (Los Angeles)": f"Cheapest flights from Austin to Los Angeles on {target_date}",
        "✈ AUS → ORD (Chicago)":     f"Cheapest flights from Austin to Chicago on {target_date}",
        "✈ AUS → JFK (New York)":    f"Cheapest flights from Austin to New York on {target_date}",
        "✈ AUS → MIA (Miami)":       f"Cheapest flights from Austin to Miami on {target_date}",
        "✈ AUS → SFO (San Francisco)": f"Cheapest flights from Austin to San Francisco on {target_date}",
    }
    for label, query in quick_routes.items():
        if st.button(label, use_container_width=True, key=label):
            st.session_state.quick_query = query

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True, help="Click to clear the conversation history and start fresh."):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### 👨‍💻 Developer")
    st.markdown("""
    **Jayshil Jain**
    - 🌐 [Website](https://jayshiljain.com)
    - 💼 [LinkedIn](https://linkedin.com/in/jayshiljain)
    - 🐙 [GitHub](https://github.com/jayshilj)
    """)
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
        if msg.get("steps"):
            with st.expander("🛠️ View Agent Data Citations & Tools"):
                for step in msg["steps"]:
                    st.markdown(f"**Tool Used:** `{step['tool']}`")
                    st.markdown(f"**Search Query:** `{step['input']}`")
                    st.markdown(f"**Data Cited:**\n```text\n{step['observation']}\n```")
        if msg.get("verifier_log"):
            with st.expander("🛡️ Guardrail Verifier Checks"):
                st.markdown(f"**Verifier Internal Log:**\n> {msg['verifier_log']}")
        st.markdown(msg["content"])

# ── API Call Helper ───────────────────────────────────────────
def call_agent(query: str, provider: str, model_name: str, api_key: str) -> dict:
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

        if "response" in data:
            return {"response": data["response"], "steps": data.get("steps", []), "verifier_log": data.get("verifier_log", "")}
        elif "detail" in data:
            return {"response": f"❌ Server error: {data['detail']}", "steps": [], "verifier_log": ""}
        else:
            return {"response": f"⚠️ Unexpected response format: {str(data)}", "steps": [], "verifier_log": ""}

    except requests.exceptions.ConnectionError:
        return {
            "response": "❌ **Cannot connect to the Flight Agent API.**\n\nMake sure FastAPI is running in your first terminal:\n```\nuvicorn app.main:app --reload\n```",
            "steps": []
        }
    except requests.exceptions.Timeout:
        return {"response": "⏱️ Request timed out. The agents are taking too long — try again.", "steps": []}
    except Exception as e:
        return {"response": f"❌ Error: {str(e)}", "steps": []}

# ── Handle Queries ────────────────────────────────────────────
def process_query(q: str):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(q)
    with st.chat_message("assistant", avatar="✈"):
        with st.spinner(f"🔍 Searching & Verifying via {provider} ({model_name})..."):
            result_data = call_agent(q, provider, model_name, user_api_key)
            
        steps = result_data.get("steps", [])
        verifier_log = result_data.get("verifier_log", "")
        
        if steps:
            with st.expander("🛠️ View Agent Data Citations & Tools"):
                for step in steps:
                    st.markdown(f"**Tool Used:** `{step['tool']}`")
                    st.markdown(f"**Search Query:** `{step['input']}`")
                    st.markdown(f"**Data Cited:**\n```text\n{step['observation']}\n```")
                    
        if verifier_log:
            with st.expander("🛡️ Guardrail Verifier Checks"):
                st.markdown(f"**Verifier Internal Log:**\n> {verifier_log}")
                
        st.markdown(result_data["response"])
        
    st.session_state.messages.append({"role": "assistant", "content": result_data["response"], "steps": steps, "verifier_log": verifier_log})

# Quick routes
if "quick_query" in st.session_state:
    query = st.session_state.pop("quick_query")
    process_query(query)
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about flights... e.g. 'Cheapest AUS to LAX on 2026-04-20'"):
    process_query(prompt)
import os
import json
import traceback
import re
import time
from typing import Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.tools.flight_search import search_flight_prices
from app.tools.hotel_search import search_hotel_prices
from app.tools.activity_search import search_local_activities

load_dotenv()

# --- LLM Factory ---
def get_llm(provider: str, model_name: str, api_key: Optional[str] = None):
    if provider == "Google":
        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-2.5-flash",
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )
    elif provider == "OpenAI":
        return ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0
        )
    elif provider == "Anthropic":
        return ChatAnthropic(
            model=model_name or "claude-3-5-sonnet-latest",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            temperature=0
        )
    elif provider == "Perplexity":
        return ChatOpenAI(
            model=model_name or "sonar",
            api_key=api_key or os.getenv("PPLX_API_KEY") or os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai",
            temperature=0
        )
    else:
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- Prompts ---
ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Trip Orchestrator Manager Agent.
Your job is to analyze the user's travel request and delegate tasks to sub-agents.
Determine if the user needs:
1. Flights (origin, destination, dates)
2. Hotels (location, dates)
3. Activities/Itinerary (location, interests)

You MUST output your decision in valid JSON format ONLY, like this:
{{
  "needs_flights": true,
  "flight_query": "Find flights from NYC to DEN on 2026-05-10",
  "needs_hotels": true,
  "hotel_query": "Find 4-star hotels in Denver from 2026-05-10 to 2026-05-14",
  "needs_activities": true,
  "activity_query": "Top things to do in Denver"
}}
If a component is not needed, set it to false and leave the query empty.
Do NOT output anything other than JSON."""),
    ("human", "{input}")
])

FLIGHT_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Flight Agent. Use search_flight_prices to find flights.
Present results in a Markdown Table format."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

HOTEL_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Hotel Agent. Use search_hotel_prices to find hotels.
Present results in a Markdown Table format."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

ACTIVITY_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Activity Agent. Use search_local_activities to find things to do.
Present results in a clean Markdown format (bullet points or numbered list)."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

VERIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Guardrail Verifier Agent for a Complete Trip system.
Your job is to review the combined output of the sub-agents (Flights, Hotels, Activities) for:
1. Accuracy: Do dates and locations match the user's request?
2. Coherence: Does the trip make logical sense?
3. Quality: Ensure hotels are highly rated (reject places with terrible reviews/low stars) and itineraries avoid generic "tourist traps" where possible.
4. Hallucinations: Ensure no fake data.

Format your entire response using the following XML tags:
<verification_log>
(Short 1-2 sentence internal log of your checks)
</verification_log>
<status>
(APPROVED if everything is good, REWORK if issues are found)
</status>
<feedback>
(If REWORK, explain exactly what the sub-agents need to fix. If APPROVED, leave empty)
</feedback>
<final_output>
(If APPROVED, the final beautifully formatted trip package. Include sections for ✈️ Flights, 🏨 Hotels, and 📍 Activities if they exist. Use Markdown tables where appropriate. If REWORK, leave empty)
</final_output>"""),
    ("human", "User Request: {query}\n\nSub-Agents Combined Response:\n{agent_response}"),
])

# --- Helper function for execution ---
def run_sub_agent(llm, tools, prompt, query, agent_name):
    try:
        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)
        
        start_time = time.time()
        res = executor.invoke({"input": query})
        elapsed_time = time.time() - start_time
        
        steps = []
        for action, observation in res.get("intermediate_steps", []):
            steps.append({
                "agent": agent_name,
                "tool": action.tool,
                "input": str(action.tool_input),
                "observation": str(observation)
            })
        
        out = res.get("output", "")
        if isinstance(out, list):
            out = " ".join([str(x) for x in out])
        else:
            out = str(out)
            
        return out, steps, elapsed_time
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error in {agent_name}: {str(e)}", [], 0.0

# --- Main Execution ---
def run_trip_agent(query: str, provider: str = "Google", model_name: str = "gemini-2.5-flash", api_key: str = None) -> dict:
    try:
        total_start_time = time.time()
        llm = get_llm(provider, model_name, api_key)
        
        timings = {
            "Trip Orchestrator": 0.0,
            "Flight Agent": 0.0,
            "Hotel Agent": 0.0,
            "Activity Agent": 0.0,
            "Guardrail Verifier": 0.0,
            "Total": 0.0
        }
        
        # 1. Orchestrator
        orch_start = time.time()
        orchestrator_chain = ORCHESTRATOR_PROMPT | llm | StrOutputParser()
        orchestrator_raw = orchestrator_chain.invoke({"input": query})
        timings["Trip Orchestrator"] += time.time() - orch_start
        
        # Parse JSON from orchestrator
        try:
            # clean potential markdown formatting
            cleaned = orchestrator_raw.strip().replace("```json", "").replace("```", "")
            plan = json.loads(cleaned)
        except Exception:
            # Fallback if it didn't output pure JSON
            plan = {"needs_flights": True, "flight_query": query, "needs_hotels": False, "needs_activities": False}
            
        all_steps = []
        all_steps.append({
            "agent": "Trip Orchestrator",
            "tool": "Analyze & Delegate",
            "input": query,
            "observation": f"Delegated tasks: Flights={plan.get('needs_flights')}, Hotels={plan.get('needs_hotels')}, Activities={plan.get('needs_activities')}"
        })

        max_retries = 2
        feedback_text = ""
        verifier_logs_combined = ""
        verified_output = ""

        for attempt in range(max_retries):
            combined_responses = []
            
            flight_q = plan.get("flight_query", "") + feedback_text if feedback_text else plan.get("flight_query", "")
            hotel_q = plan.get("hotel_query", "") + feedback_text if feedback_text else plan.get("hotel_query", "")
            activity_q = plan.get("activity_query", "") + feedback_text if feedback_text else plan.get("activity_query", "")

            # 2. Flight Agent
            if plan.get("needs_flights") and flight_q:
                flight_out, flight_steps, flight_time = run_sub_agent(llm, [search_flight_prices], FLIGHT_AGENT_PROMPT, flight_q, f"Flight Agent (Attempt {attempt+1})")
                timings["Flight Agent"] += flight_time
                combined_responses.append("--- Flights ---\n" + flight_out)
                all_steps.extend(flight_steps)

            # 3. Hotel Agent
            if plan.get("needs_hotels") and hotel_q:
                hotel_out, hotel_steps, hotel_time = run_sub_agent(llm, [search_hotel_prices], HOTEL_AGENT_PROMPT, hotel_q, f"Hotel Agent (Attempt {attempt+1})")
                timings["Hotel Agent"] += hotel_time
                combined_responses.append("--- Hotels ---\n" + hotel_out)
                all_steps.extend(hotel_steps)

            # 4. Activity Agent
            if plan.get("needs_activities") and activity_q:
                act_out, act_steps, act_time = run_sub_agent(llm, [search_local_activities], ACTIVITY_AGENT_PROMPT, activity_q, f"Activity Agent (Attempt {attempt+1})")
                timings["Activity Agent"] += act_time
                combined_responses.append("--- Activities ---\n" + act_out)
                all_steps.extend(act_steps)

            combined_text = "\n\n".join(combined_responses)
            if not combined_text:
                combined_text = "No agents were triggered based on the request."

            # 5. Verifier
            v_start = time.time()
            verifier_chain = VERIFIER_PROMPT | llm | StrOutputParser()
            verifier_raw = verifier_chain.invoke({
                "query": query,
                "agent_response": combined_text
            })
            timings["Guardrail Verifier"] += time.time() - v_start
            
            log_match = re.search(r'<verification_log>(.*?)</verification_log>', verifier_raw, re.DOTALL)
            status_match = re.search(r'<status>(.*?)</status>', verifier_raw, re.DOTALL)
            fb_match = re.search(r'<feedback>(.*?)</feedback>', verifier_raw, re.DOTALL)
            out_match = re.search(r'<final_output>(.*?)</final_output>', verifier_raw, re.DOTALL)
            
            v_log = log_match.group(1).strip() if log_match else "Verified by Guardrail."
            status = status_match.group(1).strip() if status_match else "APPROVED"
            feedback = fb_match.group(1).strip() if fb_match else ""
            
            all_steps.append({
                "agent": "Guardrail Verifier",
                "tool": f"Verify & Format (Attempt {attempt+1})",
                "input": "Combined agent outputs",
                "observation": f"Log: {v_log}\nStatus: {status}\nFeedback: {feedback}"
            })
            
            verifier_logs_combined += f"**Attempt {attempt+1}:** {v_log}\n\n"
            
            if status == "REWORK":
                feedback_text = f"\n\nGUARDRAIL FEEDBACK (You must fix this!): {feedback}"
                continue
            else:
                verified_output = out_match.group(1).strip() if out_match else combined_text
                break
        
        # If we exhausted retries and still no final output
        if not verified_output:
             verified_output = combined_text

        timings["Total"] = time.time() - total_start_time

        return {"response": verified_output, "steps": all_steps, "verifier_log": verifier_logs_combined.strip(), "timings": timings}

    except Exception as e:
        traceback.print_exc()
        return {"response": f"Agent error: {str(e)}", "steps": []}
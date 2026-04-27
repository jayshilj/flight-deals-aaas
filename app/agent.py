import os
import traceback
from typing import Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# Use langchain_classic for AgentExecutor and create_tool_calling_agent in newer LangChain versions
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.tools.flight_search import search_flight_prices

load_dotenv()

# --- LLM Factory ---
def get_llm(provider: str, model_name: str, api_key: Optional[str] = None):
    """Factory to return the correct ChatModel based on provider."""
    
    # Use provided API key or fallback to environment variables
    if provider == "Google":
        return ChatGoogleGenerativeAI(
            # Using models/ prefix can help with some versions of the SDK
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
        # WORKAROUND: ChatPerplexity in langchain-perplexity doesn't support bind_tools() yet.
        # Since Perplexity API is OpenAI-compatible, we use ChatOpenAI as a proxy.
        return ChatOpenAI(
            model=model_name or "sonar",
            api_key=api_key or os.getenv("PPLX_API_KEY") or os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai",
            temperature=0
        )
    else:
        # Default fallback
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- Prompts ---
FLIGHT_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a smart flight deals assistant powered by Google Flights data.
When users ask about flights:
1. Extract origin, destination, travel date, and trip type (one-way or round trip)
2. Convert cities to IATA codes:
   Austin/Pflugerville → AUS | Los Angeles → LAX | New York → JFK
   Chicago → ORD | Dallas → DFW | Houston → IAH | San Francisco → SFO
   Miami → MIA | Seattle → SEA | Denver → DEN | Boston → BOS
3. Call search_flight_prices with the extracted info
4. Present the final flight results exclusively in a clear, easy-to-read Markdown Table format. Include columns like Airline, Price, Departure, Arrival, Duration, Stops, and Notes. Do not use plain text lists for the flights.
5. If the user does not give a date, ask for one before searching"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

REACT_AGENT_PROMPT = PromptTemplate.from_template("""Answer the following questions as best you can using the tools provided.
When users ask about flights:
1. Extract origin, destination, travel date, and trip type (one-way or round trip)
2. Convert cities to IATA codes:
   Austin/Pflugerville → AUS | Los Angeles → LAX | New York → JFK
   Chicago → ORD | Dallas → DFW | Houston → IAH | San Francisco → SFO
   Miami → MIA | Seattle → SEA | Denver → DEN | Boston → BOS
3. Call search_flight_prices with the extracted info
4. Present the final flight results exclusively in a clear, easy-to-read Markdown Table format. Include columns like Airline, Price, Departure, Arrival, Duration, Stops, and Notes. Do not use plain text lists for the flights.
5. If the user does not give a date, ask for one before searching

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}""")

VERIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a specialized Guardrail Agent for a Flight Search system.
Your job is to review the Flight Agent's response for:
1. **Accuracy**: Does the flight info (origin/dest/date) match what the user asked for?
2. **Hallucination**: Does the response look fake? (e.g., $1 flights, nonsensical airline names).
3. **Completeness**: If flights were found, are they displayed? If not found, is it explained?
4. **Safety**: Ensure no inappropriate content.

If the response is GOOD, return it exactly as is.
If the response has ERRORS (e.g., wrong dates or hallucinated data), provide a corrected summary or explain the issue.
DO NOT mention you are a verifier in the final output unless there is a critical error.

You MUST format your entire response using the following XML tags:
<verification_log>
(Write a short 1-2 sentence internal log of your checks here. Explain if you found any errors and how you fixed them, or just state that the data passed all checks.)
</verification_log>
<final_output>
(Put the final verified response or table here. This is what the user will see.)
</final_output>"""),
    ("human", "User Request: {query}\n\nAgent Response:\n{agent_response}"),
])

# --- Agent Execution ---
def run_flight_agent(query: str, provider: str = "Google", model_name: str = "gemini-1.5-flash", api_key: str = None) -> dict:
    try:
        # 1. Initialize LLM
        llm = get_llm(provider, model_name, api_key)
        tools = [search_flight_prices]
        
        parsed_steps = []
        
        # 2. Create and Run Flight Agent
        try:
            # Perplexity has native internet access and doesn't support tools/stop words.
            # We just query it directly!
            if provider == "Perplexity":
                messages = [
                    ("system", """You are a smart flight deals assistant. The user will ask for flight information. Use your native search capabilities to find the best flights for them.
Present the final flight results exclusively in a clear, easy-to-read Markdown Table format. Include columns like Airline, Price, Departure, Arrival, Duration, Stops, and Notes. Do not use plain text lists for the flights."""),
                    ("human", query)
                ]
                response = llm.invoke(messages)
                agent_output = response.content
                parsed_steps.append({
                    "tool": "Perplexity Native Web Search",
                    "input": query,
                    "observation": "Real-time native web search results compiled internally by Perplexity."
                })
            else:
                agent = create_tool_calling_agent(llm, tools, FLIGHT_AGENT_PROMPT)
                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)
                result = agent_executor.invoke({"input": query})
                agent_output = result.get("output", "")
                
                for action, observation in result.get("intermediate_steps", []):
                    parsed_steps.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "observation": str(observation)
                    })
        except Exception as e:
            error_msg_lower = str(e).lower()
            if "custom stop words" in error_msg_lower:
                return {"response": f"❌ Error: The selected model ({provider} {model_name}) does not support custom stop words, which is required for this agent. Please try a different model.", "steps": []}
            elif isinstance(e, NotImplementedError) or "tool calling is not supported" in error_msg_lower or "does not support tool calling" in error_msg_lower:
                print(f"Falling back to ReAct agent. Reason: {e}")
                try:
                    agent = create_react_agent(llm, tools, REACT_AGENT_PROMPT)
                    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)
                    result = agent_executor.invoke({"input": query})
                    agent_output = result.get("output", "")
                    
                    for action, observation in result.get("intermediate_steps", []):
                        parsed_steps.append({
                            "tool": action.tool,
                            "input": action.tool_input,
                            "observation": str(observation)
                        })
                except Exception as react_e:
                    if "custom stop words" in str(react_e).lower():
                        return {"response": f"❌ Error: The selected model ({provider} {model_name}) does not support custom stop words, which is required for the ReAct fallback agent. Please try a different model like OpenAI or Google Gemini.", "steps": []}
                    raise react_e
            else:
                raise e
        
        if not agent_output:
            return {"response": "The agent ran but returned an empty response. Please try again.", "steps": parsed_steps}

        # 3. Verification Step (Guardrails)
        import re
        verifier_chain = VERIFIER_PROMPT | llm | StrOutputParser()
        verifier_raw = verifier_chain.invoke({
            "query": query,
            "agent_response": agent_output
        })
        
        # Parse XML tags
        log_match = re.search(r'<verification_log>(.*?)</verification_log>', verifier_raw, re.DOTALL)
        out_match = re.search(r'<final_output>(.*?)</final_output>', verifier_raw, re.DOTALL)
        
        verifier_log = log_match.group(1).strip() if log_match else "No explicit verification log provided."
        verified_output = out_match.group(1).strip() if out_match else verifier_raw.strip()
        
        return {"response": verified_output, "steps": parsed_steps, "verifier_log": verifier_log}

    except Exception as e:
        traceback.print_exc()
        return {"response": f"Agent error: {str(e)}", "steps": []}
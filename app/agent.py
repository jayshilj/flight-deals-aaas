from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.tools.flight_search import search_flight_prices
from dotenv import load_dotenv
import traceback

load_dotenv()

# ✅ 1,000 free requests/day — best free model as of March 2026
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
tools = [search_flight_prices]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a smart flight deals assistant powered by Google Flights data.
When users ask about flights:
1. Extract origin, destination, travel date, and trip type (one-way or round trip)
2. Convert cities to IATA codes:
   Austin/Pflugerville → AUS | Los Angeles → LAX | New York → JFK
   Chicago → ORD | Dallas → DFW | Houston → IAH | San Francisco → SFO
   Miami → MIA | Seattle → SEA | Denver → DEN | Boston → BOS
3. Call search_flight_prices with the extracted info
4. Present results clearly, highlight the best deal first
5. If the user does not give a date, ask for one before searching"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def run_flight_agent(query: str) -> str:
    try:
        result = agent_executor.invoke({"input": query})
        output = result.get("output", "")
        if not output:
            return "The agent ran but returned an empty response. Please try again."
        return output
    except Exception as e:
        traceback.print_exc()
        return f"Agent error: {str(e)}"
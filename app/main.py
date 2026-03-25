from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import run_flight_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="✈ Flight Deals Agent as a Service",
    description="AI-powered agent that finds the best flight deals using Amadeus API",
    version="1.0.0"
)

class FlightQuery(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "Flight Deals AaaS"}

@app.post("/ask")
def ask(request: FlightQuery):
    try:
        response = run_flight_agent(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

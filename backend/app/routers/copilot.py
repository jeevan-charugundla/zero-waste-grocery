from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from groq import Groq
from app.config import get_settings

router = APIRouter(tags=["copilot"])

class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    context: dict = Field(default_factory=dict)

class CopilotResponse(BaseModel):
    answer: str
    grounded: bool

@router.post("/copilot/answer", response_model=CopilotResponse)
def answer_question(request: CopilotRequest):
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Set GROQ_API_KEY in backend/.env.")
    # Scaffold only: replace client-supplied context with server-side Supabase queries
    # before using this endpoint for operational inventory answers.
    if not request.context:
        raise HTTPException(status_code=400, detail="No trusted data context yet. Implement server-side Supabase queries first.")
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model, temperature=0.2,
            messages=[
                {"role":"system","content":"You are a grocery operations copilot. Answer only from supplied context. If data is missing, say so. Never invent inventory, expiry, sales, savings, or consent values. Never execute actions; manager approval is required."},
                {"role":"user","content":f"Data context: {request.context}\nQuestion: {request.question}"}
            ]
        )
        return CopilotResponse(answer=response.choices[0].message.content or "No answer produced.", grounded=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Groq request failed; check server logs and API settings.") from exc

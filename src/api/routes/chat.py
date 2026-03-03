from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.knowledge import Industry
from src.services.rag import ask_question

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatRequest(BaseModel):
    industry_id: int
    question: str

class ChatResponse(BaseModel):
    answer: str
    industry_name: str

@router.post("/", response_model=ChatResponse)
def query_knowledge_base(request: ChatRequest, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == request.industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found.")
        
    try:
        answer = ask_question(industry.name, request.question)
        return ChatResponse(answer=answer, industry_name=industry.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

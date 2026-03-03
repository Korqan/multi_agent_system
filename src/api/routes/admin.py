from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from src.database import get_db
from src.models.knowledge import Industry, URLConfig
from src.vector_store.milvus_client import create_industry_collection

router = APIRouter(prefix="/api/v1/industries", tags=["admin", "industries"])

class URLConfigCreate(BaseModel):
    url: str

class URLConfigResponse(BaseModel):
    id: int
    industry_id: int
    url: str
    is_active: bool
    
    class Config:
        from_attributes = True

class IndustryCreate(BaseModel):
    name: str
    description: str | None = None

class IndustryResponse(BaseModel):
    id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True

@router.post("/", response_model=IndustryResponse, status_code=status.HTTP_201_CREATED)
def create_industry(industry_in: IndustryCreate, db: Session = Depends(get_db)):
    # Check if industry already exists
    existing = db.query(Industry).filter(Industry.name == industry_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Industry already exists.")
    
    # Create the Milvus collection for data isolation
    try:
        create_industry_collection(industry_in.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector DB collection: {e}")

    # Add to relational database tracking
    new_industry = Industry(name=industry_in.name, description=industry_in.description)
    db.add(new_industry)
    db.commit()
    db.refresh(new_industry)

    return new_industry

@router.get("/", response_model=List[IndustryResponse])
def get_industries(db: Session = Depends(get_db)):
    return db.query(Industry).all()

@router.post("/{industry_id}/urls", response_model=URLConfigResponse, status_code=status.HTTP_201_CREATED)
def add_url_config(industry_id: int, config_in: URLConfigCreate, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found.")
        
    new_url = URLConfig(industry_id=industry_id, url=config_in.url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return new_url

@router.get("/{industry_id}/urls", response_model=List[URLConfigResponse])
def get_url_configs(industry_id: int, db: Session = Depends(get_db)):
    return db.query(URLConfig).filter(URLConfig.industry_id == industry_id).all()

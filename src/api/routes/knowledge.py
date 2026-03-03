import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.knowledge import Industry, DocumentMeta
from src.services.ingestion import ingest_to_milvus, compute_file_hash

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge", "upload"])

UPLOAD_DIR = "/tmp/agent_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    industry_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validate Industry
    industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found.")
    
    # 2. Save file temporarily
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.doc', '.docx']:
        raise HTTPException(status_code=400, detail="Only PDF and Word documents are supported.")
        
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Check duplicate via Hash
    file_hash = compute_file_hash(temp_path)
    existing_doc = db.query(DocumentMeta).filter(
        DocumentMeta.file_hash == file_hash, 
        DocumentMeta.industry_id == industry_id
    ).first()
    
    if existing_doc:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="Document already exists in this industry knowledge base.")
        
    # 4. Create DB Meta Record (Status: Approved since manual upload)
    doc_meta = DocumentMeta(
        title=file.filename,
        source_type="upload",
        status="approved", # Manual uploads skip human-in-the-loop by default
        industry_id=industry_id,
        file_hash=file_hash,
        summary="Uploaded manually by user."
    )
    db.add(doc_meta)
    db.commit()
    db.refresh(doc_meta)
    
    # 5. Ingest to Milvus
    try:
        ingest_to_milvus(industry.name, str(doc_meta.id), temp_path)
    except Exception as e:
        # Rollback metadata if ingestion fails
        db.delete(doc_meta)
        db.commit()
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to process and ingest document: {str(e)}")
        
    # Clean up
    os.remove(temp_path)
    
    return {"message": "Document uploaded and ingested successfully.", "doc_id": doc_meta.id}

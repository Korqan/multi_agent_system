import os
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.services.llm import get_embeddings
from src.vector_store.milvus_client import create_industry_collection

import pdfplumber
from unstructured.partition.docx import partition_docx
import hashlib

def parse_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def parse_docx(file_path: str) -> str:
    elements = partition_docx(filename=file_path)
    text = "\n".join([str(el) for el in elements])
    return text

def compute_file_hash(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    # We create simple Document objects since we only have raw text
    return text_splitter.create_documents([text])

def ingest_to_milvus(industry_name: str, doc_id: str, file_path: str):
    """
    Parses a local file, chunks it, computes embeddings, and stores in Milvus.
    """
    # 1. Parse File
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == '.pdf':
        text = parse_pdf(file_path)
    elif ext in ['.doc', '.docx']:
        text = parse_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Must be PDF or Word.")
    
    if not text.strip():
        raise ValueError("No extractable text found in document.")

    # 2. Chunk text
    chunks = chunk_text(text)
    
    # 3. Get Embeddings
    embeddings_model = get_embeddings()
    texts = [c.page_content for c in chunks]
    vectors = embeddings_model.embed_documents(texts)
    
    # 4. Store in Milvus
    collection = create_industry_collection(industry_name)
    
    # Prepare data format for insertion
    # Using python built-in UUID for pk
    import uuid
    pks = [str(uuid.uuid4()) for _ in vectors]
    doc_ids = [str(doc_id) for _ in vectors]
    
    data = [
        pks, # pk
        texts, # text
        doc_ids, # doc_id
        vectors # vector
    ]
    
    collection.insert(data)
    collection.flush()
    print(f"Ingested {len(chunks)} chunks for document {doc_id} into collection of {industry_name}")

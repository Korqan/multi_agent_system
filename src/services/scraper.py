import requests
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.database import SessionLocal
from src.models.knowledge import URLConfig, DocumentMeta

def fetch_document_hash(content: bytes) -> str:
    hasher = hashlib.md5()
    hasher.update(content)
    return hasher.hexdigest()

def scrape_url_for_documents(url_config: URLConfig, db: Session):
    """
    Simulated scraper that visits a URL config, finds PDF/Doc links, 
    downloads them, and adds them to the Pending Review queue if new.
    """
    try:
        response = requests.get(url_config.url, timeout=10)
        response.raise_for_status()
        
        # Here we would use BeautifulSoup to find document links.
        # For demonstration, let's assume we extract a set of document URLs:
        # soup = BeautifulSoup(response.text, 'html.parser')
        # ... logic to find a tags with href ending in .pdf or .doc/x
        
        # SIMULATION of found documents at that URL for the agent system context:
        # We will just pretend we found a document link
        found_links = [
            {"url": urljoin(url_config.url, "/sample-doc.pdf"), "title": "Sample Industry Document"}
        ]
        
        for doc in found_links:
            doc_url = doc["url"]
            title = doc["title"]
            
            # Check if this URL was already scraped and approved/pending
            existing = db.query(DocumentMeta).filter(
                DocumentMeta.source_url == doc_url,
                DocumentMeta.industry_id == url_config.industry_id
            ).first()
            
            if existing: # Ideally we'd also check if the hash or Last-Modified header changed
                continue 
                
            # If it's new, we push it to Pending Review queue
            new_doc = DocumentMeta(
                title=title,
                source_url=doc_url,
                source_type="web",
                status="pending", # Human-in-the-loop requirement
                industry_id=url_config.industry_id,
                summary=f"Automated scrape from {url_config.url}."
            )
            db.add(new_doc)
            
        url_config.last_scraped_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        print(f"Error scraping {url_config.url}: {e}")

def run_scraper_job():
    """
    Cron job function to iterate through all active URLConfigs and run scraper.
    """
    print("Running scheduled scraper job...")
    db = SessionLocal()
    try:
        urls = db.query(URLConfig).filter(URLConfig.is_active == True).all()
        for url_config in urls:
            scrape_url_for_documents(url_config, db)
    finally:
        db.close()

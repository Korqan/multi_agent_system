from fastapi import FastAPI
from src.database import engine, Base

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Scenario Agent System",
    description="Agent System for Industry QA with Human-in-the-Loop scraping.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    from src.vector_store.milvus_client import connect_to_milvus
    from src.services.scheduler import start_scheduler
    try:
        connect_to_milvus()
    except Exception as e:
        print(f"Failed to connect to Milvus on startup: {e}")
        
    try:
        start_scheduler()
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    from src.services.scheduler import shutdown_scheduler
    shutdown_scheduler()

from src.api.routes import admin, knowledge, review, chat

app.include_router(admin.router)
app.include_router(knowledge.router)
app.include_router(review.router)
app.include_router(chat.router)

from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="src/frontend", html=True), name="frontend")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

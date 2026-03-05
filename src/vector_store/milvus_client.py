import os
from pymilvus import connections, utility, CollectionSchema, FieldSchema, DataType, Collection

MILVUS_HOST = os.getenv("172.21.238.107", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def connect_to_milvus():
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
    connections.connect(
        alias="default", 
        host=MILVUS_HOST, 
        port=MILVUS_PORT
    )

from src.vector_store.config import get_collection_name

def create_industry_collection(industry_name: str) -> Collection:
    """
    Retrieves a Milvus collection specifically for an industry based on config.
    It expects the collections to have been pre-initialized by init_db.py with the correct schema.
    """
    collection_name = get_collection_name(industry_name)
    
    if utility.has_collection(collection_name):
        return Collection(collection_name)
    else:
        raise ValueError(f"Collection '{collection_name}' for industry '{industry_name}' does not exist. Please run init_db.py first.")

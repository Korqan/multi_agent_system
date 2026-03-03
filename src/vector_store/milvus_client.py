import os
from pymilvus import connections, utility, CollectionSchema, FieldSchema, DataType, Collection

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def connect_to_milvus():
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
    connections.connect(
        alias="default", 
        host=MILVUS_HOST, 
        port=MILVUS_PORT
    )

def create_industry_collection(industry_name: str) -> Collection:
    """
    Creates or retrieves a Milvus collection specifically for an industry.
    This ensures data isolation per industry.
    """
    collection_name = f"knowledge_{industry_name.lower().replace(' ', '_')}"
    
    if utility.has_collection(collection_name):
        return Collection(collection_name)

    # Define schema for the industry knowledge base
    # Assuming 1536 dimension for standard embeddings like OpenAI text-embedding-ada-002 or newer equivalents
    # Adjust dim if using different models
    dim = int(os.getenv("EMBEDDING_DIM", "1536"))
    
    fields = [
        FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=100, auto_id=False),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, description="Chunk text content"),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=100, description="Reference to DocumentMeta ID"),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    
    schema = CollectionSchema(fields=fields, description=f"Knowledge Base for {industry_name}")
    
    collection = Collection(name=collection_name, schema=schema)
    
    # Create an index on the vector field
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    return collection

from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from config import INDUSTRY_MAPPING, VECTOR_DIM

def init_all_collections():
    print(">>> 开始初始化 Milvus 数据库的各个行业 Collection...")
    connections.connect(host="localhost", port="19530")

    # 定义统一的、具有极强包容性的 Schema
    fields = [
        FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4000),
        # JSON 字段是解决各行业元数据异构、标题层级不一的终极武器
        FieldSchema(name="dynamic_metadata", dtype=DataType.JSON) 
    ]
    
    schema = CollectionSchema(fields=fields, description="固定行业的结构化知识库")
    index_params = {"metric_type": "L2", "index_type": "HNSW", "params": {"M": 16, "efConstruction": 64}}

    for zh_name, en_name in INDUSTRY_MAPPING.items():
        if utility.has_collection(en_name):
            print(f"[*] 集合已存在，跳过: {zh_name} -> {en_name}")
            continue
            
        print(f"[*] 正在创建集合: {zh_name} -> {en_name}")
        collection = Collection(name=en_name, schema=schema)
        collection.create_index(field_name="vector", index_params=index_params)
        
    print(">>> 所有行业 Collection 初始化完成！")
    connections.disconnect("default")

if __name__ == "__main__":
    init_all_collections()
from pymilvus import connections, Collection, utility

print(">>> 正在连接 Milvus 数据库...")
connections.connect(alias="default", host="172.21.238.107", port="19530")

collection_names = utility.list_collections()
print(f"当前共有 {len(collection_names)} 个集合。\n")

for name in collection_names:
    print("=" * 50)
    print(f"📁 集合名称: {name}")

print("=" * 50)
connections.disconnect("default")
print(">>> 查询完毕，连接已断开。")

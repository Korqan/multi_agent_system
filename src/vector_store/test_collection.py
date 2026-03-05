from pymilvus import connections, utility

connections.connect(alias="default", host="172.21.238.107", port="19530")
all_collections = utility.list_collections()
print(f"当前数据库中共找到 {len(all_collections)} 个 Collection:")
for name in all_collections:
    print(f" - {name}")
##单文件智能解析与导入脚本
import os
import fitz  # PyMuPDF
import docx
import logging
from langchain_openai import OpenAIEmbeddings

from pymilvus import connections, Collection
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import INDUSTRY_MAPPING, VECTOR_DIM
from config import settings

logger = logging.getLogger(__name__)
# ==========================================
# 解析器 A: 处理 PDF 文档
# ==========================================
def parse_pdf(file_path):
    doc = fitz.open(file_path)
    heading_stack = [] 
    chunks = []
    doc_title = os.path.basename(file_path)
    print(file_path)
    print(len(doc))

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict").get("blocks", [])

        
        for block in blocks:
            if block.get('type') == 0: # 文本块
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        if not text: continue
                        
                        font_size = round(span["size"], 1)
                        is_bold = "Bold" in span["font"] or "Black" in span["font"]
                        
                        # 启发式规则：字号大或加粗视为标题
                        if font_size > 12 or (font_size > 10.5 and is_bold):
                            # PDF 逻辑：保留字号绝对大于当前新标题的旧标题（清空小字号）
                            heading_stack = [h for h in heading_stack if h[0] > font_size]
                            heading_stack.append((font_size, text))
                        else:
                            current_path = [h[1] for h in heading_stack]
                            chunks.append({"doc_title": doc_title, "headings_path": current_path, "text": text})
    return chunks

# ==========================================
# 解析器 B: 处理 Word (.docx) 文档
# ==========================================
def parse_docx(file_path):
    doc = docx.Document(file_path)
    heading_stack = []
    chunks = []
    doc_title = os.path.basename(file_path)

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        style_name = para.style.name
        # Word 自带结构，判断样式名是否以 'Heading' 开头
        if style_name.startswith('Heading'):
            try:
                # 提取标题级别，例如 "Heading 1" -> 1
                level = int(style_name.split(' ')[-1])
                # Word 逻辑：保留级别数字严格小于当前级别的旧标题（数字越小级别越高）
                heading_stack = [h for h in heading_stack if h[0] < level]
                heading_stack.append((level, text))
            except ValueError:
                pass # 解析失败则视为普通段落
        else:
            current_path = [h[1] for h in heading_stack]
            chunks.append({"doc_title": doc_title, "headings_path": current_path, "text": text})
            
    return chunks

# ==========================================
# 核心入库逻辑
# ==========================================
def ingest_single_document(file_path, chinese_industry_name):
    english_coll_name = INDUSTRY_MAPPING.get(chinese_industry_name)
    if not english_coll_name:
        print(f"[!] 警告: 未知行业 '{chinese_industry_name}'，跳过文件 {file_path}")
        return False

    print(f"[*] 正在解析: {file_path} -> 路由至: {english_coll_name}")
    
    # 自动识别后缀调用对应的解析器
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        extracted_data = parse_pdf(file_path)
    elif ext == 'docx':
        extracted_data = parse_docx(file_path)
    else:
        print(f"[!] 不支持的文件格式: {ext}")
        return False

    if not extracted_data:
        print("[!] 文件解析为空或未提取到有效文本。")
        return False

    rag_config = settings.config.get('rag', {})
    provider = rag_config.get('provider', 'local')
    model_name = rag_config.get('model_name', rag_config.get('embedding_model', 'all-MiniLM-L6-v2'))

    logger.info(f"📥 [RAG] 正在加载 Embedding 模型: {model_name} (Provider: {provider}) ...")
    base_url = rag_config.get('base_url', "http://localhost:8000/v1")
    api_key = rag_config.get('api_key', "EMPTY")
    logger.info("==============================")
    logger.info(base_url)
    logger.info(api_key)
    logger.info("==============================")
    model = OpenAIEmbeddings(
        model=model_name,
        openai_api_base=base_url,
        openai_api_key=api_key,
        check_embedding_ctx_length=False
    )
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    insert_data = []
    
    for item in extracted_data:
        sub_chunks = splitter.split_text(item["text"])
        if not sub_chunks:
            continue
            
        # 批量获取向量以提升速度
        vectors = model.embed_documents(sub_chunks)
        
        for idx, sub_chunk in enumerate(sub_chunks):
            metadata = {
                "doc_title": item["doc_title"],
                "headings_path": item["headings_path"],
                "source_type": ext
            }
            insert_data.append({
                "vector": vectors[idx],
                "chunk_text": sub_chunk,
                "dynamic_metadata": metadata
            })

    # 连接并写入 Milvus
    connections.connect(host="172.21.238.107", port="19530")
    collection = Collection(english_coll_name)
    
    vectors = [x["vector"] for x in insert_data]
    texts = [x["chunk_text"] for x in insert_data]
    metadatas = [x["dynamic_metadata"] for x in insert_data]
    
    collection.insert([vectors, texts, metadatas])
    collection.flush()
    connections.disconnect("default")
    print(f"[√] 成功写入 {len(vectors)} 个数据块。")
    return True

if __name__ == "__main__":
    # 单测示例
    # ingest_single_document("test_doc.pdf", "安全行业")
    pass
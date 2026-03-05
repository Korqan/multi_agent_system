from langchain_openai import OpenAIEmbeddings
import logging
from config import INDUSTRY_MAPPING, VECTOR_DIM
from config import settings

logger = logging.getLogger(__name__)
def embed_text(text): return [0.1] * VECTOR_DIM
def get_embedding_text(text):
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
    logging.info(model.embed_documents(text)[0])


if __name__ == "__main__":
    get_embedding_text("你好")
    demo = embed_text("你好")
    logger.info("==============================")
    logger.info(demo)
    logger.info("==============================")




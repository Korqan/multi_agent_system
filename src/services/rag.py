from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_milvus import Milvus
from pymilvus import Collection

from src.services.llm import get_llm, get_embeddings
from src.vector_store.milvus_client import MILVUS_HOST, MILVUS_PORT

def setup_rag_chain(industry_name: str):
    llm = get_llm(temperature=0.0)
    embeddings = get_embeddings()
    collection_name = f"knowledge_{industry_name.lower().replace(' ', '_')}"
    
    # Initialize the Milvus vector store for LangChain
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=collection_name,
        connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        vector_field="vector",
        text_field="text",
        primary_field="pk"
    )
    
    # Create the retriever (e.g., top 5 most relevant chunks)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # System prompt for RAG
    system_prompt = (
        "You are an expert AI assistant specialized in the {industry_name} industry. "
        "Use the following pieces of retrieved context to answer the user's question. "
        "If you don't know the answer based on the context, just say that you don't know, "
        "don't make up an answer. Keep the answer concise and professional.\n\n"
        "Context: {context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain
    
def ask_question(industry_name: str, question: str) -> str:
    """
    Executes the RAG pipeline for a given industry and question.
    """
    rag_chain = setup_rag_chain(industry_name)
    response = rag_chain.invoke({
        "input": question,
        "industry_name": industry_name
    })
    return response["answer"]

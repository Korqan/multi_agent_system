import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Factory function to get LLM with specific parameters
def get_llm(temperature: float = 0.0):
    return ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "dummy"), # Replace with actual key
        model="gpt-3.5-turbo", # Could be parametrized
        temperature=temperature
    )

# Factory function to get embeddings model
def get_embeddings():
    return OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_KEY", "dummy"),
        model="text-embedding-ada-002"
    )

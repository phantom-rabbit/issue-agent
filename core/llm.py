# core/llm.py
from langchain_openai import ChatOpenAI
import os

def get_llm(model_name: str = "deepseek-chat", temperature: float = 0.3):
    """
    返回一个可复用的 DeepSeek LLM 实例。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=temperature,
    )
    return llm

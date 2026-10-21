from langchain_openai import ChatOpenAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from config.settings import settings

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    base_url=settings.LANGFUSE_BASE_URL,
)

llm = ChatOpenAI(
    model=settings.MODEL_NAME,
    base_url=settings.OPENROUTER_BASE_URL,
    api_key=settings.OPENROUTER_API_KEY,
    temperature=0,
)

def langfuse_handler() -> CallbackHandler:
    """New handler per pipeline run: logs each LangChain step to Langfuse."""
    return CallbackHandler()
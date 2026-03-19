from langchain_classic.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_openai import AzureChatOpenAI

from volumes.var import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
)

# Module-level singleton — built once, reused on every call
_rag_chain = None


def get_rag_chain():
    """
    Return the cached RAG chain, building it on first call only.
    Avoids re-instantiating embeddings, vector store, and LLM on every query.
    """
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = _build_rag_chain()
    return _rag_chain


def _build_rag_chain():
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Milvus(
        collection_name="parking_info",
        embedding_function=embeddings,
    )
    llm = AzureChatOpenAI(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        temperature=0.9,
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        return_source_documents=True,
    )


def ask_chatbot(question: str) -> str:
    """
    Query the RAG chain with a user question.
    Uses the cached chain — safe to call in a tight loop without performance penalty.
    """
    chain = get_rag_chain()
    result = chain.invoke({"query": question})
    return result["result"]


# Keep build_rag_chain as a public alias for callers that need a fresh instance
# (e.g. evaluation scripts that want an isolated chain).
def build_rag_chain():
    return _build_rag_chain()

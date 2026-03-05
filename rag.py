from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_openai import AzureChatOpenAI

from volumes.var import *


def build_rag_chain():
    """
    Build the RAG (Retrieval-Augmented Generation) chain integrating vector DB and LLM.
    """
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Milvus(
        collection_name="parking_info",
        embedding_function=embeddings
    )
    # llm = OpenAI()
    llm = AzureChatOpenAI(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
        api_version=AZURE_OPENAI_API_VERSION, #"2023-12-01-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        temperature=0.9
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )
    return qa_chain

def ask_chatbot(question):
    """
    Query the RAG chain with a user question.
    :param question: User question string
    :return: Answer string
    """
    chain = build_rag_chain()
    result = chain.invoke({"query": question})
    return result['result']
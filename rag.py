from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain_openai import AzureChatOpenAI

def build_rag_chain():
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Milvus(
        collection_name="parking_info",
        embedding_function=embeddings
    )
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
    chain = build_rag_chain()
    return chain.run(question)
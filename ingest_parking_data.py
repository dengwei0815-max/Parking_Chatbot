from pymilvus import connections, Collection
from db import init_milvus, insert_data
from langchain_community.embeddings import HuggingFaceEmbeddings

collection_name = "parking_info"

# 1. Connect to Milvus first!
connections.connect("default", host="localhost", port="19530")

# 2. Drop the collection if it exists
try:
    col = Collection(collection_name)
    col.drop()
    print(f"Collection '{collection_name}' dropped.")
except Exception as e:
    print(f"Collection '{collection_name}' does not exist or could not be dropped: {e}")

# 3. Now initialize the collection with the correct schema
collection = init_milvus()

# 4. Prepare your data
parking_data = [
    "The parking lot is located at 123 Main Street.",
    "Parking is available 24 hours a day.",
    "The hourly parking rate is $2.",
    "There are 50 parking spaces available.",
    "To reserve a parking space, provide your name, car number, and reservation period."
]

# 5. Generate embeddings
embeddings_model = HuggingFaceEmbeddings()
embeddings = [embeddings_model.embed_query(text) for text in parking_data]

# 6. Insert data
insert_data(collection, embeddings, parking_data)

print("✅ Data ingestion complete! Your parking info is now in Milvus.")
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

def init_milvus():
    """
    Initialize Milvus connection and collection.
    """
    connections.connect("default", host="localhost", port="19530")
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=500)
    ]
    schema = CollectionSchema(fields, "Parking Info Collection")
    collection = Collection("parking_info", schema)
    return collection

def insert_data(collection, embeddings, texts):
    """
    Insert data into Milvus collection.
    :param collection: Milvus collection object
    :param embeddings: List of embeddings
    :param texts: List of texts
    """
    collection.insert([embeddings, texts])
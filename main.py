from pymongo import MongoClient
import os

def connection():
# MongoDB connection details
    connectionString = os.environ.get("MONGODB_URI")
    database_name = "Nutrients"
    collection_name = "all"
    collection_name2 = "missing_ingredients"
    try:
        client = MongoClient(connectionString)
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

    database = client[database_name]
    collection = database[collection_name]
    collection2 = database[collection_name2]
    return collection , collection2

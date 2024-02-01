from pymongo import MongoClient

def get_mongo_db():
    # Replace the placeholder values with your MongoDB connection details
    # connection_string = "mongodb://username:password@localhost:27017/mydatabase"
    connection_string = "mongodb+srv://yasith:Q4EMtZzs2RGFcfIb@onionlk.1iqmvcm.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)

    # Access your database (create it if it doesn't exist)
    db = client.mydatabase
    return db

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Connect to MongoDB (Defaults to local if MONGO_URL is missing)
mongo_url = os.getenv("MONGO_URL")
if mongo_url:
    client = AsyncIOMotorClient(mongo_url)
else:
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
    print("⚠️ Using Mock MongoDB for testing.")

db = client.telepathology_db

# Collections
users = db.users
cases = db.cases
transfers = db.transfers
logs = db.system_logs
messages = db.messages
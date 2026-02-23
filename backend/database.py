from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Connect to MongoDB (Defaults to local if MONGO_URL is missing)
client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client.telepathology_db

# Collections
users = db.users
cases = db.cases
transfers = db.transfers
logs = db.system_logs
messages = db.messages
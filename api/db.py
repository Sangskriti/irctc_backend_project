import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME")]

# Collections defined here
users_col = db["users"]
trains_col = db["trains"]
bookings_col = db["bookings"]
logs_col = db["logs"]
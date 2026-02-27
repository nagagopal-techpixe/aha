# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb+srv://nagagopalchimata566_db_user:ek51dcOsE23SXZqz@cluster0.tpviehp.mongodb.net/movie_reviews?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.movie_reviews
review_collection = database.get_collection("reviews")
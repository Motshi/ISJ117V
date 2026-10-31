from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

users_collection = db["Users"]
cvs_collection = db["CVs"]
extracted_skills_collection = db["ExtractedSkills"]
jobs_collection = db["Jobs"]
job_matches_collection = db["JobMatches"]
applications_collection = db["Applications"]


async def ensure_indexes():
    await users_collection.create_index("email", unique=True)
    await cvs_collection.create_index("user_id")
    await extracted_skills_collection.create_index("user_id")
    await job_matches_collection.create_index("user_id")
    await applications_collection.create_index("user_id")

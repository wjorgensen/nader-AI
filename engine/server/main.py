from fastapi import FastAPI, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import os
from engine.packages.mongo import MDB
from typing import Annotated
import asyncio
from functools import wraps
from bson import ObjectId
import json

# Custom JSON encoder to handle ObjectId serialization
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to run pymongo operations asynchronously
async def run_in_threadpool(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

# MongoDB dependency
def get_mongo():
    mongo = MDB()
    mongo.connect()
    try:
        yield mongo
    finally:
        mongo.close()

# Pydantic model for job submission
class JobSubmission(BaseModel):
    companyName: str
    companyDescription: str
    jobDescription: str
    calComLink: str
    contactEmail: str

# Pydantic model for job stored in DB
class Job(JobSubmission):
    status: str = "not started"
    created_at: datetime = Field(default_factory=datetime.now)

@app.get("/")
def root():
    return "/"

@app.post("/api/jobs")
async def create_job(
    job_data: JobSubmission = Body(...),
    mongo: MDB = Depends(get_mongo)
):
    # Convert to Job model with default status
    job = Job(**job_data.model_dump())
    job_dict = job.model_dump()
    
    job_collection = mongo.client.job_board.jobs
    result = await asyncio.to_thread(
        lambda: job_collection.insert_one(job_dict)
    )
    
    # Convert ObjectId to string to make it JSON serializable
    job_id = str(result.inserted_id)
    
    # Create a new dictionary with only JSON-serializable values
    response_dict = {
        "id": job_id,
        "message": "Job submitted successfully",
        "companyName": job_dict["companyName"],
        "companyDescription": job_dict["companyDescription"],
        "jobDescription": job_dict["jobDescription"],
        "calComLink": job_dict["calComLink"],
        "contactEmail": job_dict["contactEmail"],
        "status": job_dict["status"],
        "created_at": job_dict["created_at"].isoformat()  # Convert datetime to ISO string
    }
    
    return response_dict
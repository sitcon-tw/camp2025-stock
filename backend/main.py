# 範例程式
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# client = AsyncIOMotorClient("mongodb://localhost:27017")
# db = client["mydatabase"]

@app.get("/api/hello")
async def say_hello():
    return {"message": "Hello from FastAPI"}

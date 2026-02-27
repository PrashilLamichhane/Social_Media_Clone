from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate
from app.db import create_db_and_tables, get_async_session, Post
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

text_post = {
    1: {"title": "First Post", "content": "This is the content for the first post."},
    2: {"title": "Morning Thoughts", "content": "Every morning is a new chance to start fresh."},
    3: {"title": "Daily Motivation", "content": "Small steps every day lead to big results."},
    4: {"title": "Tech Talk", "content": "Technology moves fast—keep learning or fall behind."},
    5: {"title": "Life Lesson", "content": "Failure is not the opposite of success; it’s part of it."},
    6: {"title": "Quick Reminder", "content": "Don’t forget to take breaks and breathe."},
    7: {"title": "Creative Spark", "content": "Ideas grow when you give them time and attention."},
    8: {"title": "Productivity Tip", "content": "Focus on finishing, not perfecting."},
    9: {"title": "Evening Reflection", "content": "What you did today matters more than what you planned."},
    10: {"title": "Final Thought", "content": "Consistency beats intensity in the long run."}
}


@app.get("/posts")
def get_posts():
    return text_post

@app.get("/posts/{id}")
def get_post_by_id(id :int ):

    if id not in text_post:
        
        raise HTTPException(status_code=404, detail="Post not found")
    
    else: 

         return text_post[id]
    

@app.post("/posts")
def create_post(post: PostCreate):
    new_post = {
        "title": post.title,
        "content": post.content
    }
    text_post[max(text_post.keys()) + 1] = new_post



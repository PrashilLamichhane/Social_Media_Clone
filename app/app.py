import shutil
from sys import exception
import tempfile
from unittest import result

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate
from app.db import create_db_and_tables, get_async_session, Post, User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.image import imagekit
from app.schemas import UserRead, UserCreate, UserUpdate
import shutil, os, uuid, tempfile
from app.users import auth_backend, fastapi_users, current_active_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead,UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])

@app.post("/upload")
async def upload_file(
    file : UploadFile = File(...),
    caption: str = Form(...),
    user: User = Depends(current_active_user),
    session:AsyncSession = Depends(get_async_session)
):
    
    temp_file_path = None
    temp_file_obj = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            # Copy the uploaded file content to the temp file
            shutil.copyfileobj(file.file, temp_file)
       
        # Open the temp file for upload
        temp_file_obj = open(temp_file_path, "rb")
        
        # Upload to ImageKit using the correct SDK method
        upload_result = imagekit.files.upload(
            file=temp_file_obj,
            file_name=file.filename,
        )
        
        # If upload is successful, the result object will have file_id, url, etc.
        # If there's an error, an exception will be raised
        if upload_result and upload_result.file_id:
            # Create post in database
            post = Post(
                caption=caption, 
                user_id=user.id,
                url=upload_result.url,
                file_type= "video" if file.content_type.startswith("video/") else "image",
                file_name=upload_result.name
            )
            
            # Update the session
            session.add(post)
            await session.commit()
            await session.refresh(post)
            
            return {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "file_id": upload_result.file_id
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="ImageKit upload failed - no file_id returned"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    finally:
        # Close the temp file object if it was opened
        if temp_file_obj:
            temp_file_obj.close()
        
        # Delete the temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # Close the uploaded file
        file.file.close()
    


@app.get("/feed")
async def get_feed(
    session:AsyncSession = Depends(get_async_session), 
    user: User = Depends(current_active_user)
    ):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.fetchall()]
    result = await session.execute(select(User).where(User.id.in_([post.user_id for post in posts])))
    users = [row[0] for row in result.fetchall()]
    user_dict = {user.id: user for user in users}

    post_data = []
    for post in posts:
        post_data.append({
            "id": str(post.id),
            "user_id": str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "is_owner": post.user_id == user.id,
            "email": user_dict[post.user_id].email if post.user_id in user_dict else None
        })
    return {"posts": post_data}

@app.delete("/delete/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        # Delete from ImageKit
        await session.delete(post)
        await session.commit()
        return {"detail": "Post deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")
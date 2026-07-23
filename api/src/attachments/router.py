import os
import uuid
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.attachments.models import Attachment
from src.attachments.schemas import AttachmentOut
from src.auth.dependencies import get_current_user, get_user_or_bot
from src.auth.models import User
from src.config import settings

router = APIRouter(prefix="/attachments", tags=["attachments"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_user_or_bot)
):
    """
    Upload a file and create an Attachment record.
    Returns the Attachment object.
    """
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    bytes_read = 0

    with open(file_path, "wb") as f:
        while content_chunk := await file.read(1024 * 1024):
            bytes_read += len(content_chunk)
            if bytes_read > max_size:
                f.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
                )
            f.write(content_chunk)

    attachment = Attachment(
        filename=file.filename or unique_filename,
        file_path=file_path.replace("\\", "/"),
        content_type=file.content_type or "application/octet-stream"
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return attachment

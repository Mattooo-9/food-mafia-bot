import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from backend.api.deps import CurrentUser
from backend.api.schemas import UploadOut
from backend.config import settings

router = APIRouter(tags=["uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload", response_model=UploadOut)
async def upload_photo(file: UploadFile, user: CurrentUser) -> UploadOut:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Допустимы только изображения JPG/PNG/WebP")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    data = await file.read()
    if len(data) > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="Файл слишком большой (максимум 5 МБ)")

    filename = f"{user.id}_{secrets.token_hex(8)}{ext}"
    path = settings.upload_dir / filename
    path.write_bytes(data)
    return UploadOut(url=f"/uploads/{filename}")

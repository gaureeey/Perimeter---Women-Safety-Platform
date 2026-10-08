"""
PERIMETER Platform — Device Media Upload & Validation Engine
Handles secure device file uploads (camera, gallery, file picker),
enforces strict MIME/extension/size validation, and stores files locally
with UUID sanitization.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List, Optional
import os
import uuid
from app.core.security import get_optional_user
from app.models.user import User

router = APIRouter(prefix="/media", tags=["Media Upload & Storage"])

# Directory configuration
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Validation rules
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
ALLOWED_VIDEO_MIMES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB

FORBIDDEN_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".php", ".py", ".js", ".html",
    ".htm", ".svg", ".dll", ".so", ".jar", ".vbs", ".ps1"
}

def validate_and_save_file(file: UploadFile) -> dict:
    original_filename = file.filename or "upload.bin"
    ext = os.path.splitext(original_filename)[1].lower()

    if ext in FORBIDDEN_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security alert: Executable or script file extension '{ext}' is forbidden."
        )

    content_type = (file.content_type or "").lower()

    # Determine media type
    if ext in ALLOWED_IMAGE_EXTENSIONS or content_type in ALLOWED_IMAGE_MIMES:
        media_type = "image"
        max_size = MAX_IMAGE_SIZE
    elif ext in ALLOWED_VIDEO_EXTENSIONS or content_type in ALLOWED_VIDEO_MIMES:
        media_type = "video"
        max_size = MAX_VIDEO_SIZE
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media type. Allowed formats: JPG, PNG, WEBP, GIF, MP4, WEBM, MOV."
        )

    # Read and validate file size
    try:
        contents = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    size = len(contents)
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    if size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb} MB."
        )

    # Generate secure unique filename
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(dest_path, "wb") as f:
        f.write(contents)

    return {
        "url": f"/uploads/{unique_filename}",
        "filename": unique_filename,
        "original_name": original_filename,
        "media_type": media_type,
        "size_bytes": size,
        "content_type": content_type
    }

@router.post("/upload")
def upload_single_media(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload a single photo or video from device camera/gallery/file-picker.
    """
    result = validate_and_save_file(file)
    if current_user:
        result["uploaded_by"] = current_user.name
    return result

@router.post("/upload-multiple")
def upload_multiple_media(
    files: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload multiple photos or videos (carousel support, up to 10 items).
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 media items allowed per post."
        )

    uploaded_items = []
    urls = []
    for f in files:
        item = validate_and_save_file(f)
        uploaded_items.append(item)
        urls.append(item["url"])

    return {
        "count": len(uploaded_items),
        "items": uploaded_items,
        "urls": urls
    }

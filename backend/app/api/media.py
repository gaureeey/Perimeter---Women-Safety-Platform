from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pathlib import Path
import uuid

router = APIRouter(prefix="/media", tags=["Media Uploads"])

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
ALLOWED = {
    "post": {
        "image/jpeg", "image/png", "image/webp", "image/gif"
    },
    "story": {
        "image/jpeg", "image/png", "image/webp", "image/gif"
    },
    "sos": {
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/webm",
        "video/mp4", "video/webm", "video/quicktime", "video/x-matroska"
    }
}
MAX_BYTES = 25 * 1024 * 1024

@router.post("/upload")
async def upload_media(
    request: Request,
    kind: str = "post",
    file: UploadFile = File(...)
):
    kind = kind.lower().strip()
    if kind not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid upload type.")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED[kind]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Posts accept images; SOS proof accepts audio/video."
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 25 MB.")

    suffix = Path(file.filename or "").suffix.lower()
    if not suffix:
        suffix = {
            "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
            "image/gif": ".gif", "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
            "audio/wav": ".wav", "audio/ogg": ".ogg", "audio/webm": ".webm",
            "video/mp4": ".mp4", "video/webm": ".webm",
            "video/quicktime": ".mov", "video/x-matroska": ".mkv"
        }.get(content_type, ".bin")

    folder = UPLOAD_ROOT / kind
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = folder / filename
    target.write_bytes(data)

    return {
        "url": f"{str(request.base_url).rstrip('/')}/media/{kind}/{filename}",
        "filename": filename,
        "content_type": content_type,
        "size": len(data),
        "kind": kind
    }

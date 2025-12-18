from fastapi import APIRouter, File, UploadFile, HTTPException, status
import os
import shutil
import uuid
from pathlib import Path
from app.services.file_storage import save_uploaded_file

router = APIRouter(prefix="/upload", tags=["uploads"])

MEDIA_DIR = Path("app") / "media"

@router.post("/bytes")
async def upload_bytes(file: bytes = File(...)):
    return {
        "filename":"archivo_subido",
        "size_byte":len(file)
    }

@router.post("/file")
async def upload_file(file: UploadFile=File(...)):
    return {
        "filename":file.filename,
        "content_type":file.content_type
    }
    
@router.post("/save")
async def save_file(file: UploadFile):
    saved = save_uploaded_file(file)

    return {
        "filename": saved["filename"],
        "content_type": saved["content_type"],
        "url":saved["url"]
    }
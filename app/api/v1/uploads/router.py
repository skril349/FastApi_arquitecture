from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/upload", tags=["uploads"])

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

import os
from pathlib import Path
from urllib.request import Request

from fastapi import FastAPI, File, UploadFile, HTTPException
from .ocr_engine import SynapseOCRv3_2_0
from .security import verify_internal_call

PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_ROOT / "ocr_uploads"

app = FastAPI(
    title="OCR Service",
    description="Internal OCR processing service",
    version="1.0.0"
)


@app.middleware("http")
async def internal_request_middleware(request: Request, call_next):
    # Skip docs / health
    if request.url.path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)

    key = request.headers.get("x-internal-key")

    if not verify_internal_call(key):
        raise HTTPException(status_code=403, detail="Forbidden")

    return await call_next(request)

@app.post("/ocr")
async def process_ocr(
        file: UploadFile = File(...),
):

    # Process OCR
    try:
        # Create upload directory
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Generate filename
        original_name = file.filename
        file_path = os.path.join(UPLOAD_DIR, original_name)

        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as destination:
            destination.write(contents)

        ocr = SynapseOCRv3_2_0()
        result = ocr.extract_text_optimized_v3(file_path)

        if result['success']:
            return {
                'confidence': result['confidence'],
                'time': result['processing_time'],
                'raw_text': result['raw_text'],
                'normalized_text': result['normalized_text'],
                'bounding_boxes': len(result.get('bounding_boxes', [])),
                'method': f"OCR:{result['version']}:{result['strategy']}",
                'file_path': file_path,
            }

        raise HTTPException(status_code=500, detail=f"OCR processing failed!")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
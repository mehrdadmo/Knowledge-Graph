import os

INTERNAL_API_KEY = os.getenv("OCR_INTERNAL_API_KEY")

def verify_internal_call(x_internal_key: str) -> bool:
    if not INTERNAL_API_KEY:
        return False

    if not x_internal_key:
        return False

    return x_internal_key == INTERNAL_API_KEY

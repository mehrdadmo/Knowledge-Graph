import logging
import os
from typing import Any, Dict, Union

import requests
import urllib3
from requests.adapters import HTTPAdapter

from services.interfaces.ocr_core_interface import OCRCoreInterface

logger = logging.getLogger('tesseract3.2_ocr_core')


class Tesseract32OCRCoreService(OCRCoreInterface):
    def __init__(self) -> None:
        self.url = os.environ.get('OCR_CORE_URL', 'http://127.0.0.1:8765/ocr')
        self.key = os.environ.get('OCR_INTERNAL_API_KEY', 'MAke_me_HARd_SOmethiiing')
        self.timeout = 300

    def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Union[Dict, str, None]:
        """
        Make API request with authentication

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint

        Returns:
            Response data or None if failed
        """
        try:
            session = requests.Session()

            # Start with authentication headers
            headers = {
                "accept": "application/json",
                "x-internal-key": self.key,
            }

            # For non-file requests, add JSON content type
            if 'files' not in kwargs:
                headers["Content-Type"] = "application/json"

            response = session.request(
                method, endpoint, headers=headers, timeout=self.timeout,
                verify=False, **kwargs
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"OCR Core API request failed: {str(e)}", exc_info=True)
            return None

    def process_doc(self, file: Any) -> Union[Dict, bool]:
        """
        Send file to Core OCR service

        Returns:
            Dict: Response from server containing process status and data
        """
        try:
            # For file uploads, use the 'files' parameter instead of 'json'
            result = self._make_request("POST", self.url, files={'file': file})

            if result is None:
                logger.error("Failed to create ocr_Core request.")
                return False

            return result

        except Exception as e:
            logger.error(f"Failed to create customer: {str(e)}", exc_info=True)
            return False

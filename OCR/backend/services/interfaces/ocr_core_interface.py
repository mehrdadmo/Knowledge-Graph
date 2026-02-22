from abc import ABC, abstractmethod
from typing import Dict, Any


class OCRCoreInterface(ABC):
    @abstractmethod
    def process_doc(self, file: Any) -> Dict:
        pass

from curl_cffi import requests
from typing import Optional


class DocumentService:
    DOCUMENT_API_URL = "https://portal.scscourt.org/api/doc/base64/doc"
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
    
    def get_document_base64(self, document_id: str) -> Optional[str]:
        try:
            decoded_doc_id = document_id.replace("%3D", "=").replace("%2B", "+").replace("%2F", "/")
            
            response = requests.get(
                self.DOCUMENT_API_URL,
                params={"docId": decoded_doc_id},
                impersonate="chrome",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                base64_content = response_data.get("data", {}).get("bytes")
                if base64_content:
                    return base64_content
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            return None

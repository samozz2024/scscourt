from curl_cffi import requests
from typing import Optional
from utils.logger import ColorLogger


class TokenService:
    TOKEN_URL = "https://portal.scscourt.org/api/case/token"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def get_token(self, recaptcha_code: str) -> Optional[str]:
        try:
            headers = {"recaptcha": recaptcha_code}
            
            response = requests.get(
                self.TOKEN_URL,
                headers=headers,
                impersonate="chrome",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                token = response.json().get("token")
                if token:
                    ColorLogger.success("Token retrieved")
                    return token
                else:
                    ColorLogger.error("Token not found in response")
                    return None
            else:
                ColorLogger.error(f"Token request failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            ColorLogger.error(f"Token request error: {e}")
            return None

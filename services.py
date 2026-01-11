from captchatools import new_harvester
from curl_cffi import requests
from typing import Optional, Dict, Any
from logger import ColorLogger


class CaptchaService:
    def __init__(self, api_key: str, sitekey: str, captcha_url: str):
        self.api_key = api_key
        self.sitekey = sitekey
        self.captcha_url = captcha_url
    
    def solve_captcha(self) -> Optional[str]:
        try:
            harvester = new_harvester(
                api_key=self.api_key,
                solving_site="capsolver",
                captcha_type="v2",
                sitekey=self.sitekey,
                captcha_url=self.captcha_url,
            )
            token = harvester.get_token()
            ColorLogger.success("reCAPTCHA solved")
            return token
        except Exception as e:
            error_msg = str(e)
            if "Invalid API key" in error_msg or "api key" in error_msg.lower():
                ColorLogger.error(f"CapSolver API key error: {e}")
                ColorLogger.error(f"API key starts with: {self.api_key[:10]}...")
            else:
                ColorLogger.error(f"reCAPTCHA failed: {e}")
            raise


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


class CaseService:
    CASE_API_URL = "https://portal.scscourt.org/api/case/{case_id}"
    
    def __init__(self, timeout: int = 30, use_proxy: bool = False, proxy_url: str = ""):
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
    
    def get_case_data(self, case_id: str, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {"case-token": token}
            proxies = None
            
            if self.use_proxy and self.proxy_url:
                proxies = {
                    "http": self.proxy_url,
                    "https": self.proxy_url,
                }
            
            url = self.CASE_API_URL.format(case_id=case_id)
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                impersonate="chrome",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == 0:
                    return data
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            return None


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

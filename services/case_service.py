from curl_cffi import requests
from typing import Optional, Dict, Any


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

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ScraperConfig:
    capsolver_api_key: str
    recaptcha_sitekey: str
    recaptcha_url: str
    
    proxy_url: str
    use_proxy: bool
    
    supabase_url: str
    supabase_key: str
    
    case_workers: int
    document_workers: int
    max_retries: int
    
    token_refresh_interval: int
    captcha_buffer_size: int
    
    request_timeout: int
    
    @classmethod
    def from_env(cls):
        return cls(
            capsolver_api_key=os.getenv("CAPSOLVER_API_KEY", ""),
            recaptcha_sitekey=os.getenv("RECAPTCHA_SITEKEY", "6Lej28wUAAAAAAa44bVlVhkJrBDvVNIW2Wpdphx3"),
            recaptcha_url=os.getenv("RECAPTCHA_URL", "https://portal.scscourt.org/search"),
            
            proxy_url=os.getenv("PROXY_URL", ""),
            use_proxy=os.getenv("USE_PROXY", "true").lower() == "true",
            
            supabase_url=os.getenv("SUPABASE_URL", "https://bxhcubpqxbfysudhchjx.supabase.co"),
            supabase_key=os.getenv("SUPABASE_KEY", ""),
            
            case_workers=int(os.getenv("CASE_WORKERS", "3")),
            document_workers=int(os.getenv("DOCUMENT_WORKERS", "5")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            
            token_refresh_interval=int(os.getenv("TOKEN_REFRESH_INTERVAL", "600")),
            captcha_buffer_size=int(os.getenv("CAPTCHA_BUFFER_SIZE", "2")),
            
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "60")),
        )

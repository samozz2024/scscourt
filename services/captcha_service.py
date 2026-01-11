from captchatools import new_harvester
from typing import Optional
from utils.logger import ColorLogger


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
            ColorLogger.error(f"reCAPTCHA failed: {e}")
            return None

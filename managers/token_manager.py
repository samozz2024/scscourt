import threading
import time
from typing import Optional
from queue import Queue
from services.captcha_service import CaptchaService
from services.token_service import TokenService
from utils.logger import ColorLogger


class TokenManager:
    def __init__(
        self,
        captcha_service: CaptchaService,
        token_service: TokenService,
        refresh_interval: int = 600,
        buffer_size: int = 2
    ):
        self.captcha_service = captcha_service
        self.token_service = token_service
        self.refresh_interval = refresh_interval
        self.buffer_size = buffer_size
        
        self.captcha_buffer = Queue(maxsize=buffer_size)
        self.current_token: Optional[str] = None
        self.token_lock = threading.Lock()
        
        self._stop_event = threading.Event()
        self._captcha_thread: Optional[threading.Thread] = None
        self._token_refresh_thread: Optional[threading.Thread] = None
    
    def start(self):
        ColorLogger.info("Starting Token Manager...")
        
        ColorLogger.info(f"Pre-filling captcha buffer ({self.buffer_size} solutions)...")
        for i in range(self.buffer_size):
            captcha_code = self.captcha_service.solve_captcha()
            if captcha_code:
                self.captcha_buffer.put(captcha_code)
                ColorLogger.success(f"Captcha {i+1}/{self.buffer_size} buffered")
            else:
                ColorLogger.error(f"Captcha {i+1}/{self.buffer_size} failed")
        
        initial_captcha = self.captcha_buffer.get()
        self.current_token = self.token_service.get_token(initial_captcha)
        
        if not self.current_token:
            raise RuntimeError("Failed to obtain initial token")
        
        ColorLogger.success("Initial token obtained")
        
        self._captcha_thread = threading.Thread(target=self._captcha_worker, daemon=True)
        self._captcha_thread.start()
        
        self._token_refresh_thread = threading.Thread(target=self._token_refresh_worker, daemon=True)
        self._token_refresh_thread.start()
        
        ColorLogger.success("Token Manager started")
    
    def stop(self):
        ColorLogger.info("Stopping Token Manager...")
        self._stop_event.set()
        if self._captcha_thread:
            self._captcha_thread.join(timeout=5)
        if self._token_refresh_thread:
            self._token_refresh_thread.join(timeout=5)
        ColorLogger.success("Token Manager stopped")
    
    def get_token(self) -> Optional[str]:
        with self.token_lock:
            return self.current_token
    
    def _captcha_worker(self):
        while not self._stop_event.is_set():
            try:
                if not self.captcha_buffer.full():
                    captcha_code = self.captcha_service.solve_captcha()
                    if captcha_code:
                        self.captcha_buffer.put(captcha_code)
                        ColorLogger.success(f"Captcha buffered ({self.captcha_buffer.qsize()}/{self.buffer_size})")
                    else:
                        ColorLogger.warning("Captcha failed, retrying in 10s...")
                        time.sleep(10)
                else:
                    time.sleep(5)
            except Exception as e:
                ColorLogger.error(f"Captcha worker error: {e}")
                time.sleep(10)
    
    def _token_refresh_worker(self):
        while not self._stop_event.is_set():
            time.sleep(self.refresh_interval)
            
            if self._stop_event.is_set():
                break
            
            ColorLogger.info("Refreshing token...")
            
            try:
                captcha_code = self.captcha_buffer.get(timeout=60)
                new_token = self.token_service.get_token(captcha_code)
                
                if new_token:
                    with self.token_lock:
                        self.current_token = new_token
                    ColorLogger.success("Token refreshed")
                else:
                    ColorLogger.error("Token refresh failed, keeping old token")
                    self.captcha_buffer.put(captcha_code)
                    
            except Exception as e:
                ColorLogger.error(f"Token refresh error: {e}")

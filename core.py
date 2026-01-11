import threading
import time
from typing import Optional, Dict, Any, List
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from services import CaptchaService, TokenService, DocumentService
from logger import ColorLogger


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


class CaseProcessor:
    def __init__(self, document_service: DocumentService, document_workers: int = 5, max_retries: int = 3):
        self.document_service = document_service
        self.document_workers = document_workers
        self.max_retries = max_retries
    
    def process_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_number = case_data.get("data", {}).get("caseNumber", "Unknown")
        
        document_ids = self._extract_document_ids(case_data)
        
        if not document_ids:
            ColorLogger.info(f"{case_number}: No documents")
            return case_data
        
        ColorLogger.processing(f"{case_number}: Downloading {len(document_ids)} documents...")
        
        document_map = self._download_documents(document_ids, case_number)
        
        self._inject_documents_into_case(case_data, document_map)
        
        ColorLogger.success(f"{case_number}: {len(document_map)}/{len(document_ids)} documents downloaded")
        
        return case_data
    
    def _extract_document_ids(self, case_data: Dict[str, Any]) -> List[str]:
        document_ids = []
        data = case_data.get("data", {})
        
        for event in data.get("caseEvents", []):
            for doc in event.get("documents", []):
                doc_id = doc.get("documentId")
                if doc_id:
                    document_ids.append(doc_id)
        
        for hearing in data.get("caseHearings", []):
            for doc in hearing.get("documents", []):
                doc_id = doc.get("documentId")
                if doc_id:
                    document_ids.append(doc_id)
        
        return document_ids
    
    def _download_documents(self, document_ids: List[str], case_number: str) -> Dict[str, str]:
        document_map = {}
        
        with ThreadPoolExecutor(max_workers=self.document_workers) as executor:
            future_to_doc_id = {
                executor.submit(self._download_document_with_retry, doc_id): doc_id
                for doc_id in document_ids
            }
            
            for future in as_completed(future_to_doc_id):
                doc_id = future_to_doc_id[future]
                try:
                    base64_content = future.result()
                    if base64_content:
                        document_map[doc_id] = base64_content
                except Exception as e:
                    pass
        
        return document_map
    
    def _download_document_with_retry(self, document_id: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            base64_content = self.document_service.get_document_base64(document_id)
            if base64_content:
                return base64_content
        
        return None
    
    def _inject_documents_into_case(self, case_data: Dict[str, Any], document_map: Dict[str, str]):
        data = case_data.get("data", {})
        
        for event in data.get("caseEvents", []):
            for doc in event.get("documents", []):
                doc_id = doc.get("documentId")
                if doc_id and doc_id in document_map:
                    doc["pdf_base64"] = document_map[doc_id]
        
        for hearing in data.get("caseHearings", []):
            for doc in hearing.get("documents", []):
                doc_id = doc.get("documentId")
                if doc_id and doc_id in document_map:
                    doc["pdf_base64"] = document_map[doc_id]

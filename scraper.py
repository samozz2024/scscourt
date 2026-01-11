import csv
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from colorama import Fore, Style, init

from configuration import ScraperConfig
from services import CaptchaService, TokenService, CaseService, DocumentService
from core import TokenManager, CaseProcessor
from database import SupabaseRepository
from logger import ColorLogger

init(autoreset=True)


class CourtScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        
        self.captcha_service = CaptchaService(
            api_key=config.capsolver_api_key,
            sitekey=config.recaptcha_sitekey,
            captcha_url=config.recaptcha_url
        )
        
        self.token_service = TokenService(timeout=config.request_timeout)
        
        self.token_manager = TokenManager(
            captcha_service=self.captcha_service,
            token_service=self.token_service,
            refresh_interval=config.token_refresh_interval,
            buffer_size=config.captcha_buffer_size
        )
        
        self.case_service = CaseService(
            timeout=config.request_timeout,
            use_proxy=config.use_proxy,
            proxy_url=config.proxy_url
        )
        
        self.document_service = DocumentService(timeout=config.request_timeout)
        
        self.case_processor = CaseProcessor(
            document_service=self.document_service,
            document_workers=config.document_workers,
            max_retries=config.max_retries
        )
        
        self.repository = SupabaseRepository(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_key
        )
        
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_documents": 0,
            "documents_downloaded": 0,
            "documents_failed_download": 0,
            "documents_uploaded": 0,
            "documents_failed_upload": 0
        }
        
        self.failed_cases = []
        self.stats_lock = threading.Lock()
    
    def run(self, case_ids_file: str):
        start_time = time.time()
        start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._print_header(start_datetime)
        
        try:
            self.token_manager.start()
            
            case_ids = self._load_case_ids(case_ids_file)
            self.stats["total"] = len(case_ids)
            
            ColorLogger.info(f"Loaded {len(case_ids)} case IDs")
            
            self._process_cases(case_ids)
            
        except KeyboardInterrupt:
            ColorLogger.warning("Interrupted by user")
        except Exception as e:
            ColorLogger.error(f"Fatal error: {e}")
        finally:
            self.token_manager.stop()
            self.repository.close()
            
            end_time = time.time()
            end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            
            self._print_summary(start_datetime, end_datetime, duration)
    
    def _load_case_ids(self, file_path: str) -> List[str]:
        case_ids = []
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    case_ids.append(row[0].strip())
        return case_ids
    
    def _process_cases(self, case_ids: List[str]):
        ColorLogger.info(f"Processing with {self.config.case_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.config.case_workers) as executor:
            future_to_case_id = {
                executor.submit(self._process_single_case, case_id): case_id
                for case_id in case_ids
            }
            
            for future in as_completed(future_to_case_id):
                case_id = future_to_case_id[future]
                try:
                    future.result()
                except Exception as e:
                    ColorLogger.error(f"Case {case_id}: {e}")
                    self.stats["failed"] += 1
                    self.failed_cases.append(case_id)
    
    def _process_single_case(self, case_id: str):
        for attempt in range(self.config.max_retries):
            try:
                token = self.token_manager.get_token()
                if not token:
                    if attempt < self.config.max_retries - 1:
                        ColorLogger.warning(f"Case {case_id}: No token available, retrying...")
                        time.sleep(3)
                        continue
                    else:
                        ColorLogger.error(f"Case {case_id}: No token after {self.config.max_retries} attempts")
                        with self.stats_lock:
                            self.stats["failed"] += 1
                            self.failed_cases.append(case_id)
                        return
                
                case_data = self.case_service.get_case_data(case_id, token)
                
                if not case_data or not case_data.get("data"):
                    if attempt < self.config.max_retries - 1:
                        ColorLogger.warning(f"Case {case_id}: Fetch failed, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        ColorLogger.error(f"Case {case_id}: Failed after {self.config.max_retries} attempts")
                        with self.stats_lock:
                            self.stats["failed"] += 1
                            self.failed_cases.append(case_id)
                        return
                
                case_number = case_data.get("data", {}).get("caseNumber")
                if not case_number:
                    ColorLogger.error(f"Case {case_id}: No case number in response")
                    with self.stats_lock:
                        self.stats["failed"] += 1
                        self.failed_cases.append(case_id)
                    return
                
                if self.repository.case_exists(case_number):
                    ColorLogger.skip(f"{case_number}: Already exists")
                    with self.stats_lock:
                        self.stats["skipped"] += 1
                    return
                
                processed_case, doc_stats = self.case_processor.process_case(case_data)
                
                save_result = self.repository.save_case(processed_case)
                
                with self.stats_lock:
                    self.stats["total_documents"] += doc_stats["total"]
                    self.stats["documents_downloaded"] += doc_stats["downloaded"]
                    self.stats["documents_failed_download"] += doc_stats["failed"]
                    self.stats["documents_uploaded"] += save_result["doc_stats"]["uploaded"]
                    self.stats["documents_failed_upload"] += save_result["doc_stats"]["failed"]
                
                if save_result["success"]:
                    ColorLogger.success(f"{case_number}: Saved to Supabase")
                    with self.stats_lock:
                        self.stats["success"] += 1
                    return
                else:
                    if attempt < self.config.max_retries - 1:
                        ColorLogger.warning(f"{case_number}: Save failed, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        ColorLogger.error(f"{case_number}: Save failed after {self.config.max_retries} attempts")
                        with self.stats_lock:
                            self.stats["failed"] += 1
                            self.failed_cases.append(case_id)
                        return
                
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    ColorLogger.warning(f"Case {case_id}: Error - {e}, retrying...")
                    time.sleep(2)
                else:
                    ColorLogger.error(f"Case {case_id}: {e}")
                    with self.stats_lock:
                        self.stats["failed"] += 1
                        self.failed_cases.append(case_id)
    
    def _print_header(self, start_datetime: str):
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'California Court Scraper':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Start Time: {start_datetime}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Case Workers: {self.config.case_workers} | Document Workers: {self.config.document_workers}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Token Refresh: Every {self.config.token_refresh_interval}s | Max Retries: {self.config.max_retries}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    def _print_summary(self, start_datetime: str, end_datetime: str, duration: float):
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        cases_per_min = (self.stats['success'] / (duration / 60)) if duration > 0 else 0
        docs_per_min = (self.stats['documents_downloaded'] / (duration / 60)) if duration > 0 else 0
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'SCRAPING SUMMARY':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}⏱  Start Time:     {start_datetime}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⏱  End Time:       {end_datetime}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⏱  Duration:       {minutes}m {seconds}s ({duration:.2f} seconds){Style.RESET_ALL}")
        print(f"{Fore.CYAN}⚡ Speed:          {cases_per_min:.2f} cases/min | {docs_per_min:.2f} docs/min{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'CASES':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}📊 Total Cases:    {self.stats['total']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓  Success:        {self.stats['success']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⊘  Skipped:        {self.stats['skipped']}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗  Failed:         {self.stats['failed']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'DOCUMENTS':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}📄 Total Documents:        {self.stats['total_documents']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}⬇  Downloaded:             {self.stats['documents_downloaded']}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗  Failed Download:        {self.stats['documents_failed_download']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}⬆  Uploaded to Storage:    {self.stats['documents_uploaded']}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗  Failed Upload:          {self.stats['documents_failed_upload']}{Style.RESET_ALL}")
        
        download_rate = (self.stats['documents_downloaded'] / self.stats['total_documents'] * 100) if self.stats['total_documents'] > 0 else 0
        upload_rate = (self.stats['documents_uploaded'] / self.stats['documents_downloaded'] * 100) if self.stats['documents_downloaded'] > 0 else 0
        
        print(f"\n{Fore.CYAN}{'PERFORMANCE':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}📈 Download Success Rate:  {download_rate:.1f}%{Style.RESET_ALL}")
        print(f"{Fore.WHITE}📈 Upload Success Rate:    {upload_rate:.1f}%{Style.RESET_ALL}")
        
        if self.failed_cases:
            print(f"\n{Fore.CYAN}{'FAILED CASES':^80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
            for case_id in self.failed_cases:
                print(f"{Fore.RED}  ✗ {case_id}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

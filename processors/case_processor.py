from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.document_service import DocumentService
from utils.logger import ColorLogger


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

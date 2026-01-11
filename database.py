import base64
import re
from typing import Dict, Any, List
from supabase import create_client, Client
from logger import ColorLogger


class SupabaseRepository:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "documents"
    
    def save_case(self, case_data: Dict[str, Any]) -> bool:
        try:
            data = case_data.get("data", {})
            case_number = data.get("caseNumber")
            
            if not case_number:
                ColorLogger.error("Case data missing caseNumber")
                return False
            
            self._save_case_info(data, case_number)
            self._save_parties(data, case_number)
            self._save_attorneys(data, case_number)
            self._save_hearings(data, case_number)
            self._save_documents(data, case_number)
            
            return True
                
        except Exception as e:
            ColorLogger.error(f"Supabase save error: {e}")
            return False
    
    def case_exists(self, case_number: str) -> bool:
        try:
            response = self.client.table("cases").select("case_number").eq("case_number", case_number).execute()
            return len(response.data) > 0
        except Exception as e:
            return False
    
    def _save_case_info(self, data: Dict[str, Any], case_number: str):
        case_record = {
            "case_number": case_number,
            "type": data.get("type"),
            "style": data.get("style"),
            "file_date": data.get("fileDate"),
            "status": data.get("status"),
            "court_location": data.get("courtLocation")
        }
        
        self.client.table("cases").upsert(case_record, on_conflict="case_number").execute()
    
    def _save_parties(self, data: Dict[str, Any], case_number: str):
        parties = data.get("caseParties", [])
        
        self.client.table("parties").delete().eq("case_number", case_number).execute()
        
        for party in parties:
            party_record = {
                "case_number": case_number,
                "type": party.get("type"),
                "first_name": party.get("firstName"),
                "middle_name": party.get("middleName"),
                "last_name": party.get("lastName"),
                "nick_name": party.get("nickName"),
                "business_name": party.get("businessName"),
                "full_name": party.get("fullName"),
                "is_defendant": party.get("isDefendant")
            }
            
            self.client.table("parties").insert(party_record).execute()
    
    def _save_attorneys(self, data: Dict[str, Any], case_number: str):
        attorneys = data.get("caseAttornies", [])
        
        self.client.table("attorneys").delete().eq("case_number", case_number).execute()
        
        for attorney in attorneys:
            attorney_record = {
                "case_number": case_number,
                "first_name": attorney.get("firstName"),
                "middle_name": attorney.get("middleName"),
                "last_name": attorney.get("lastName"),
                "representing": attorney.get("representing"),
                "bar_number": attorney.get("barNumber"),
                "is_lead": attorney.get("isLead")
            }
            
            self.client.table("attorneys").insert(attorney_record).execute()
    
    def _save_hearings(self, data: Dict[str, Any], case_number: str):
        hearings = data.get("caseHearings", [])
        
        self.client.table("hearings").delete().eq("case_number", case_number).execute()
        
        for hearing in hearings:
            hearing_record = {
                "case_number": case_number,
                "hearing_id": hearing.get("hearingId"),
                "calendar": hearing.get("calendar"),
                "type": hearing.get("type"),
                "date": hearing.get("date"),
                "time": hearing.get("time"),
                "hearing_result": hearing.get("hearingResult")
            }
            
            self.client.table("hearings").insert(hearing_record).execute()
    
    def _save_documents(self, data: Dict[str, Any], case_number: str):
        document_list = []
        
        for event in data.get("caseEvents", []):
            for doc in event.get("documents", []):
                doc_id = doc.get("documentId")
                doc_name = doc.get("documentName")
                pdf_base64 = doc.get("pdf_base64")
                
                if doc_id and doc_name:
                    document_list.append({
                        "documentId": doc_id,
                        "documentName": doc_name,
                        "pdf_base64": pdf_base64
                    })
        
        for hearing in data.get("caseHearings", []):
            for doc in hearing.get("documents", []):
                doc_id = doc.get("documentId")
                doc_name = doc.get("documentName")
                pdf_base64 = doc.get("pdf_base64")
                
                if doc_id and doc_name:
                    document_list.append({
                        "documentId": doc_id,
                        "documentName": doc_name,
                        "pdf_base64": pdf_base64
                    })
        
        if document_list:
            self.client.table("documents").delete().eq("case_number", case_number).execute()
        
        for doc in document_list:
            clean_name = self._clean_document_name(doc["documentName"])
            
            doc_record = {
                "case_number": case_number,
                "document_name": clean_name
            }
            
            try:
                self.client.table("documents").insert(doc_record).execute()
                
                if doc.get("pdf_base64"):
                    self._upload_pdf_to_storage(case_number, clean_name, doc["pdf_base64"])
            except Exception as e:
                ColorLogger.warning(f"Failed to save document {clean_name}: {e}")
    
    def _clean_document_name(self, name: str) -> str:
        name = re.sub(r'[(),."\']+', '', name)
        name = name.replace(' ', '-')
        
        if not name.lower().endswith('.pdf'):
            name += '.pdf'
        
        return name
    
    def _upload_pdf_to_storage(self, case_number: str, document_name: str, base64_content: str):
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                pdf_bytes = base64.b64decode(base64_content)
                file_path = f"{case_number}/{document_name}"
                
                self.client.storage.from_(self.bucket_name).upload(
                    file_path,
                    pdf_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"}
                )
                
                time.sleep(0.1)
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    ColorLogger.warning(f"Failed to upload {document_name}: {e}")
    
    def close(self):
        ColorLogger.success("Supabase connection closed")

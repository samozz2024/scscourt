from pymongo import MongoClient
from typing import Dict, Any
from logger import ColorLogger


class CaseRepository:
    def __init__(self, mongodb_uri: str, database: str, collection: str):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database]
        self.collection = self.db[collection]
    
    def save_case(self, case_data: Dict[str, Any]) -> bool:
        try:
            data = case_data.get("data", {})
            case_number = data.get("caseNumber")
            
            if not case_number:
                ColorLogger.error("Case data missing caseNumber")
                return False
            
            document = {
                "_id": case_number,
                **data
            }
            
            self.collection.replace_one(
                {"_id": case_number},
                document,
                upsert=True
            )
            
            return True
                
        except Exception as e:
            ColorLogger.error(f"MongoDB save error: {e}")
            return False
    
    def case_exists(self, case_number: str) -> bool:
        try:
            return self.collection.count_documents({"_id": case_number}, limit=1) > 0
        except Exception as e:
            return False
    
    def close(self):
        try:
            self.client.close()
            ColorLogger.success("MongoDB connection closed")
        except Exception as e:
            ColorLogger.error(f"MongoDB close error: {e}")

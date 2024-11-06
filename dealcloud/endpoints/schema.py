from typing import Dict, List, Optional
from dealcloud.endpoints.base import APIEndpoint

class SchemaEndpoint(APIEndpoint):
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to a schema endpoint"""
        return self._make_request("GET", endpoint, params=params)

    def get_entry_types(self) -> List[Dict]:
        """Get all entry types"""
        return self.get("/api/rest/v4/schema/entryTypes")

    def get_entry_type_fields(self, entry_type_id: int) -> List[Dict]:
        """Get fields for a specific entry type"""
        return self.get(f"/api/rest/v4/schema/entryTypes/{entry_type_id}/fields")

    def get_all_fields(self) -> List[Dict]:
        """Get all fields across all entry types"""
        return self.get("/api/rest/v4/schema/allfields")

    # ... rest of SchemaEndpoint methods ... 
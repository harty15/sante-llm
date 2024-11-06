from typing import Dict, List, Optional
import json
from dealcloud.endpoints.base import APIEndpoint

class DataEndpoint(APIEndpoint):
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to a data endpoint"""
        return self._make_request("GET", endpoint, params=params)

    def get_entries(self, entry_type_id: int, query: Optional[Dict] = None, fields: Optional[List[str]] = None) -> Dict:
        """
        Get entries for a specific entry type with optional query and field filtering
        """
        params = {"wrapIntoArrays": "true"}
        if query:
            params["query"] = json.dumps(query)
        if fields:
            params["fields"] = ",".join(fields)
        return self.get(f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", params=params)

    def create_entries(self, entry_type_id: int, entries: List[Dict]) -> List[Dict]:
        """Create new entries"""
        return self._make_request("POST", f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", data=entries)

    def update_entries(self, entry_type_id: int, entries: List[Dict]) -> List[Dict]:
        """Update existing entries"""
        return self._make_request("PATCH", f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", data=entries)

    def delete_entries(self, entry_type_id: int, entry_ids: List[int]) -> List[Dict]:
        """Delete entries by ID"""
        return self._make_request("DELETE", f"/api/rest/v4/data/entrydata/{entry_type_id}", data=entry_ids)

    # ... rest of DataEndpoint methods ... 
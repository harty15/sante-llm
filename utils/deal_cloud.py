import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import fuzzywuzzy

class TokenManager:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def get_valid_token(self) -> str:
        if self._is_token_valid():
            return self.access_token
        elif self.refresh_token:
            self._refresh_token()
        else:
            self._request_new_token()
        return self.access_token

    def _is_token_valid(self) -> bool:
        return self.access_token and self.token_expiry and datetime.now() < self.token_expiry

    def _request_new_token(self) -> None:
        url = f"{self.base_url}/api/rest/v1/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "data user_management"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        self._update_token_info(response.json())

    def _refresh_token(self) -> None:
        url = f"{self.base_url}/api/rest/v1/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        self._update_token_info(response.json())

    def _update_token_info(self, token_data: Dict[str, Any]) -> None:
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])

class APIEndpoint(ABC):
    def __init__(self, token_manager: TokenManager, base_url: str):
        self.token_manager = token_manager
        self.base_url = base_url

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token_manager.get_valid_token()}"}
        response = requests.request(method, url, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def get(self, *args, **kwargs):
        pass

class SchemaEndpoint(APIEndpoint):
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return self._make_request("GET", endpoint, params=params)

    def get_entry_types(self) -> List[Dict]:
        return self.get("/api/rest/v4/schema/entryTypes")

    def get_entry_type_fields(self, entry_type_id: int) -> List[Dict]:
        return self.get(f"/api/rest/v4/schema/entryTypes/{entry_type_id}/fields")

    def get_all_fields(self) -> List[Dict]:
        return self.get("/api/rest/v4/schema/allfields")

class DataEndpoint(APIEndpoint):
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return self._make_request("GET", endpoint, params=params)

    def get_entries(self, entry_type_id: int, query: Optional[Dict] = None, fields: Optional[List[str]] = None) -> Dict:
        params = {"wrapIntoArrays": "true"}
        if query:
            params["query"] = json.dumps(query)
        if fields:
            params["fields"] = ",".join(fields)
        return self.get(f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", params=params)

    def create_entries(self, entry_type_id: int, entries: List[Dict]) -> List[Dict]:
        return self._make_request("POST", f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", data=entries)

    def update_entries(self, entry_type_id: int, entries: List[Dict]) -> List[Dict]:
        return self._make_request("PATCH", f"/api/rest/v4/data/entrydata/rows/{entry_type_id}", data=entries)

    def delete_entries(self, entry_type_id: int, entry_ids: List[int]) -> List[Dict]:
        return self._make_request("DELETE", f"/api/rest/v4/data/entrydata/{entry_type_id}", data=entry_ids)

class UserManagementEndpoint(APIEndpoint):
    def get(self, params: Optional[Dict] = None) -> List[Dict]:
        return self._make_request("GET", "/api/rest/v1/management/user", params=params)

    def get_users(self, modified_since: Optional[str] = None, email: Optional[str] = None) -> List[Dict]:
        params = {}
        if modified_since:
            params["modifiedSince"] = modified_since
        if email:
            params["email"] = email
        return self.get(params=params)

    def create_user(self, user_data: Dict) -> Dict:
        return self._make_request("POST", "/api/rest/v1/management/user", data=user_data)

    def update_user(self, user_data: Dict) -> Dict:
        return self._make_request("PUT", "/api/rest/v1/management/user", data=user_data)

    def delete_user(self, user_id: int) -> None:
        self._make_request("DELETE", f"/api/rest/v1/management/user?userId={user_id}")

class DealCloudAPI:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.token_manager = TokenManager(client_id, client_secret, base_url)
        self.schema = SchemaEndpoint(self.token_manager, base_url)
        self.data = DataEndpoint(self.token_manager, base_url)
        self.user_management = UserManagementEndpoint(self.token_manager, base_url)

base_url = "https://sante.dealcloud.com"
client_id = "1018744"
client_secret = "cpawBni/6RmBAe2UEkL3lK/XrG/uWMexIE6a8R9TpXw="

api = DealCloudAPI(client_id=client_id, client_secret=client_secret, base_url=base_url)


def find_user_by_email(api: DealCloudAPI, email: str) -> Optional[Dict]:
    users = api.user_management.get_users(email=email)
    if users:
        return users[0]  # Return the first user found
    else:
        print(f"User with email '{email}' not found.")
        return None
    
    
email_to_search = "ryan.harty@sante.com"
user = find_user_by_email(api, email_to_search)

if user:
    print(f"User found: {user['firstName']} {user['lastName']}")
else:
    print("User not found")


def find_contact_by_name_and_email(
    api: DealCloudAPI,
    first_name: str,
    last_name: str,
    email: Optional[str] = None
) -> Optional[Dict]:
    try:
        # Get the Contact entry type
        contact_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )
        
        # Build query based on available information
        query = {}
        if email:
            # If email is available, use it as primary search criterion
            query = {"EmailAddress": {"$eq": email}}
        else:
            # Otherwise search by first and last name
            query = {
                "$and": [
                    {"FirstName": {"$contains": first_name}},
                    {"LastName": {"$contains": last_name}}
                ]
            }
        
        contacts = api.data.get_entries(contact_entry_type['id'], query=query)
        
        if not contacts.get('rows'):
            return None
            
        # If searching by email, return first match
        if email and contacts['rows']:
            return contacts['rows'][0]
            
        # If searching by name, use fuzzy matching to find best match
        full_name = f"{first_name} {last_name}".lower()
        
        potential_matches = []
        for contact in contacts['rows']:
            contact_full_name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".lower()
            ratio = fuzz.ratio(full_name, contact_full_name)
            if ratio > 85:  # Set threshold for name matching
                potential_matches.append((contact, ratio))
        
        if potential_matches:
            # Return the contact with highest match ratio
            best_match = max(potential_matches, key=lambda x: x[1])
            return best_match[0]
            
        return None

    except Exception as e:
        print(f"Error searching for contact: {str(e)}")
        return None
    

first_name = "Andrew"
last_name = "Cohen"
contact = find_contact_by_name_and_email(api, first_name, last_name)


def get_user_ids_by_email(api: DealCloudAPI, emails: List[str]) -> List[int]:
    """
    Look up user IDs - modified to use data API instead of user management
    """
    try:
        # Get the User entry type
        user_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'User'
        )
        
        user_ids = []
        for email in emails:
            query = {"Email": {"$eq": email}}
            user = api.user_management.get_users(email=email)
            user_ids.append(user[0]['id'])
        return user_ids
    except Exception as e:
        print(f"Error looking up users by email: {str(e)}")
        return []
    
def find_user_by_email(api: DealCloudAPI, email: str) -> Optional[Dict]:
    users = api.user_management.get_users(email=email)
    if users:
        return users[0]  # Return the first user found
    else:
        print(f"User with email '{email}' not found.")
        return None
    
    
email_to_search = "ryan.harty@sante.com"
user = find_user_by_email(api, email_to_search)

if user:
    print(f"User found: {user['firstName']} {user['lastName']}")
else:
    print("User not found")
    
get_user_ids_by_email(api, ['ryan.harty@sante.com'])


from typing import Optional, Dict, List, Union
from fuzzywuzzy import fuzz
from deal_cloud_client import DealCloudAPI

def find_company_by_name(api: DealCloudAPI, company_name: str) -> Optional[Dict]:
    """
    Find a company by name using fuzzy matching
    """
    try:
        # Get the Company entry type
        company_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Company' or et['singularName'] == 'Company'
        )
        
        # Query for companies with similar names
        query = {"CompanyName": {"$contains": company_name[:3]}}  # Use first 3 chars to broaden search
        companies = api.data.get_entries(company_entry_type['id'], query=query)
        
        if not companies.get('rows'):
            return None
            
        # Use fuzzy matching to find best match
        potential_matches = []
        for company in companies['rows']:
            company_name_field = company.get('CompanyName', {})
            if isinstance(company_name_field, dict):
                actual_name = company_name_field.get('name', '')
            else:
                actual_name = str(company_name_field)
                
            if actual_name:
                ratio = fuzz.ratio(company_name.lower(), actual_name.lower())
                if ratio > 85:  # Set threshold for match
                    potential_matches.append((company, ratio))
        
        if potential_matches:
            # Return the company with highest match ratio
            best_match = max(potential_matches, key=lambda x: x[1])
            return best_match[0]
            
        return None

    except Exception as e:
        print(f"Error searching for company: {str(e)}")
        return None

def find_contact_by_name_and_email(
    api: DealCloudAPI,
    first_name: str,
    last_name: str,
    email: Optional[str] = None
) -> Optional[Dict]:
    """
    Find a contact by name and/or email
    """
    try:
        # Get the Contact entry type
        contact_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )
        
        # Build query based on available information
        query = {}
        if email:
            # If email is available, use it as primary search criterion
            query = {"Email": {"$eq": email}}
        else:
            # Otherwise search by first and last name
            query = {
                "$and": [
                    {"FirstName": {"$contains": first_name}},
                    {"LastName": {"$contains": last_name}}
                ]
            }
        
        contacts = api.data.get_entries(contact_entry_type['id'], query=query)
        
        if not contacts.get('rows'):
            return None
            
        # If searching by email, return first match
        if email and contacts['rows']:
            return contacts['rows'][0]
            
        # If searching by name, use fuzzy matching to find best match
        full_name = f"{first_name} {last_name}".lower()
        
        potential_matches = []
        for contact in contacts['rows']:
            contact_full_name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".lower()
            ratio = fuzz.ratio(full_name, contact_full_name)
            if ratio > 85:  # Set threshold for name matching
                potential_matches.append((contact, ratio))
        
        if potential_matches:
            # Return the contact with highest match ratio
            best_match = max(potential_matches, key=lambda x: x[1])
            return best_match[0]
            
        return None

    except Exception as e:
        print(f"Error searching for contact: {str(e)}")
        return None

def get_choice_field_id(api: DealCloudAPI, entry_type_id: int, field_name: str, choice_value: str) -> Optional[int]:
    """
    Get the ID for a choice field value
    """
    try:
        fields = api.schema.get_entry_type_fields(entry_type_id)
        field = next((f for f in fields if f['apiName'] == field_name), None)
        
        if field and field.get('choiceValues'):
            choice = next((c for c in field['choiceValues'] if c['name'].lower() == choice_value.lower()), None)
            if choice:
                return choice['id']
    except Exception as e:
        print(f"Error getting choice field ID for {field_name}: {str(e)}")
    return None

def get_country_id(api: DealCloudAPI, country_name: str) -> Optional[int]:
    """
    Get country ID from the Country reference
    """
    try:
        # Get the Contact entry type to get the Country field info
        contact_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )
        
        # Get the Country field from Contact entry type
        fields = api.schema.get_entry_type_fields(contact_entry_type['id'])
        country_field = next((f for f in fields if f['apiName'] == 'Country'), None)
        
        if country_field:
            # Get all entries for the country entry type
            countries = api.data.get_entries(country_field['entryLists'][0])
            if countries.get('rows'):
                country = next(
                    (c for c in countries['rows'] 
                     if c.get('Name', {}).get('name', '').lower() == country_name.lower()),
                    None
                )
                if country:
                    return country['EntryId']
    except Exception as e:
        print(f"Error getting country ID: {str(e)}")
    return None

def get_title_id(api: DealCloudAPI, title: str) -> Optional[int]:
    """
    Get title ID - removing creation since it's likely restricted
    """
    try:
        # Get the Contact entry type to get the Title field info
        contact_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )
        
        # Get the Title field from Contact entry type
        fields = api.schema.get_entry_type_fields(contact_entry_type['id'])
        title_field = next((f for f in fields if f['apiName'] == 'Title'), None)
        
        if title_field:
            # Get all entries for the title entry type
            titles = api.data.get_entries(title_field['entryLists'][0])
            if titles.get('rows'):
                title_entry = next(
                    (t for t in titles['rows'] 
                     if t.get('Name', {}).get('name', '').lower() == title.lower()),
                    None
                )
                if title_entry:
                    return title_entry['EntryId']
    except Exception as e:
        print(f"Error getting title ID: {str(e)}")
    return None

def get_user_ids_by_email(api: DealCloudAPI, emails: List[str]) -> List[int]:
    """
    Look up user IDs - modified to use data API instead of user management
    """
    try:
        # Get the User entry type
        user_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'User'
        )
        
        user_ids = []
        for email in emails:
            query = {"Email": {"$eq": email}}
            user = api.user_management.get_users(email=email)
            user_ids.append(user[0]['id'])
        return user_ids
    except Exception as e:
        print(f"Error looking up users by email: {str(e)}")
        return []

def create_company(
    api: DealCloudAPI,
    company_name: str,
    company_type: Optional[str] = None,
    website: Optional[str] = None,
    coverage_status: str = "Never Contacted",
    owner_emails: Optional[List[str]] = None,
) -> Optional[Dict]:
    """
    Create a new company using the cells endpoint
    """
    try:
        # Get the Company entry type
        company_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Company' or et['singularName'] == 'Company'
        )
        print(f"Found company entry type: {company_entry_type}")
        
        # Check if company already exists
        existing_company = find_company_by_name(api, company_name)
        if existing_company:
            print(f"Found existing company: {company_name}")
            return existing_company, "existing"
            
        # Get field definitions
        fields = api.schema.get_entry_type_fields(company_entry_type['id'])
        
        # Create store requests array
        store_requests = []
        entry_id = -1
        
        # Add CompanyName
        store_requests.append({
            "value": company_name,
            "ignoreNearDups": True,
            "entryId": entry_id,
            "fieldId": next(f['id'] for f in fields if f['apiName'] == 'CompanyName')
        })
        
        # Add Database (required)
        database_field = next(f for f in fields if f['apiName'] == 'Database')
        database_value = next(cv['id'] for cv in database_field['choiceValues'] if cv['name'] == 'No')
        store_requests.append({
            "value": database_value,
            "ignoreNearDups": True,
            "entryId": entry_id,
            "fieldId": database_field['id']
        })
        
        # Add CoverageStatus
        coverage_field = next(f for f in fields if f['apiName'] == 'CoverageStatus')
        coverage_value = next(cv['id'] for cv in coverage_field['choiceValues'] if cv['name'] == coverage_status)
        store_requests.append({
            "value": coverage_value,
            "ignoreNearDups": True,
            "entryId": entry_id,
            "fieldId": coverage_field['id']
        })
        
        # Add Website if provided
        if website:
            website_field = next(f for f in fields if f['apiName'] == 'Website')
            store_requests.append({
                "value": website,
                "ignoreNearDups": True,
                "entryId": entry_id,
                "fieldId": website_field['id']
            })
        
        # Add Type if provided
        if company_type:
            type_field = next(f for f in fields if f['apiName'] == 'Type')
            type_value = next((cv['id'] for cv in type_field['choiceValues'] 
                             if cv['name'].lower() == company_type.lower()), None)
            if type_value:
                store_requests.append({
                    "value": type_value,
                    "ignoreNearDups": True,
                    "entryId": entry_id,
                    "fieldId": type_field['id']
                })
                
                # Also set TypePrimarySecondary
                type_ps_field = next(f for f in fields if f['apiName'] == 'TypePrimarySecondary')
                store_requests.append({
                    "value": type_value,
                    "ignoreNearDups": True,
                    "entryId": entry_id,
                    "fieldId": type_ps_field['id']
                })
        
        # Add Owners if provided
        if owner_emails:
            owner_ids = get_user_ids_by_email(api, owner_emails)
            if owner_ids:
                owners_field = next((f for f in fields if f['apiName'] == 'CreatedBy'), None)
                if owners_field:
                    store_requests.append({
                        "value": owner_ids,
                        "ignoreNearDups": True,
                        "entryId": entry_id,
                        "fieldId": owners_field['id']
                    })
                    
        print(f"Creating company with store requests: {store_requests}")
        
        # Create the company using cells endpoint
        url = f"{api.token_manager.base_url}/api/rest/v4/data/entrydata/{company_entry_type['id']}"
        headers = {"Authorization": f"Bearer {api.token_manager.get_valid_token()}"}
        response = requests.post(
            url,
            json={"storeRequests": store_requests},
            headers=headers
        )
        response.raise_for_status()
        created_data = response.json()
        
        if created_data:
            print(f"Successfully created company: {company_name}")
            # Get the created company data
            new_company_id = created_data[0]['rowId']
            company_data = api.data.get_entries(company_entry_type['id'], 
                                              query={"EntryId": new_company_id})
            if company_data and company_data.get('rows'):
                return company_data['rows'][0], "created"
        
        print("Failed to create company - no response from API")
        return None, "failed"
            
    except Exception as e:
        print(f"Error creating company: {str(e)}")
        print("Response content:", getattr(locals().get('response'), 'content', None))
        import traceback
        traceback.print_exc()
        return None, "error"

def create_contact_with_company(
    api: DealCloudAPI,
    first_name: str,
    last_name: str,
    email: Optional[str] = None,
    company_name: Optional[str] = None,
    job_title: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    notes: Optional[str] = None,
    salutation: Optional[str] = None,
    contact_type: Optional[str] = None,
    company_type: Optional[str] = None,
    website: Optional[str] = None,
    country: Optional[str] = None,
    owner_emails: Optional[List[str]] = None,
    primary_contact: bool = True,
    globally_unsubscribed: bool = False,
    additional_emails: bool = False
) -> Optional[Dict]:
    """
    Create a contact and its associated company if needed
    """
    try:
        # First try to find or create the company if company_name is provided
        company_id = None
        if company_name:
            print(f"Looking up/creating company: {company_name}")
            company, company_status = create_company(
                api=api,
                company_name=company_name,
                company_type=company_type,
                website=website,
                owner_emails=owner_emails
            )
            
            if company and company_status in ["existing", "created"]:
                print(f"Got company with status {company_status}")
                company_id = company.get('EntryId')
                if not company_id:
                    print("Company found but no EntryId present")
                    return None, "company_invalid"
            else:
                print(f"Company creation failed with status: {company_status}")
                return None, "company_failed"
            
        # Get the Contact entry type
        contact_entry_type = next(
            et for et in api.schema.get_entry_types() 
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )
        
        # Check if contact already exists
        existing_contact = find_contact_by_name_and_email(api, first_name, last_name, email)
        if existing_contact:
            print(f"Found existing contact: {first_name} {last_name}")
            return existing_contact, "existing"
            
        # Get all fields for the contact entry type
        contact_fields = api.schema.get_entry_type_fields(contact_entry_type['id'])
        
        # Get choice field values
        salutation_field = next((f for f in contact_fields if f['apiName'] == 'Salutation'), None)
        contact_type_field = next((f for f in contact_fields if f['apiName'] == 'ContactType'), None)
        primary_contact_field = next((f for f in contact_fields if f['apiName'] == 'PrimaryContact'), None)
        
        # Find choice values
        salutation_value = None
        if salutation_field and salutation:
            salutation_value = next((cv['id'] for cv in salutation_field.get('choiceValues', []) 
                                   if cv['name'].lower() == salutation.lower()), None)
            
        contact_type_value = None
        if contact_type_field and contact_type:
            contact_type_value = next((cv['id'] for cv in contact_type_field.get('choiceValues', []) 
                                     if cv['name'].lower() == contact_type.lower()), None)
            
        primary_contact_value = None
        if primary_contact_field:
            primary_contact_value = next((cv['id'] for cv in primary_contact_field.get('choiceValues', []) 
                                        if cv['name'].lower() == ('yes' if primary_contact else 'no').lower()), None)
        
        # Get reference IDs
        country_id = get_country_id(api, country) if country else None
        title_id = get_title_id(api, job_title) if job_title else None
        owner_ids = get_user_ids_by_email(api, owner_emails) if owner_emails else None

        # Prepare contact data
        new_contact = {
            "EntryId": -1,
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "GloballyUnsubscribed": globally_unsubscribed,
            "AdditionalEmails": additional_emails
        }

        # Add optional fields if their IDs were found
        if company_id:
            new_contact["Company"] = company_id
        if salutation_value:
            new_contact["Salutation"] = salutation_value
        if contact_type_value:
            new_contact["ContactType"] = contact_type_value
        if country_id:
            new_contact["Country"] = country_id
        if title_id:
            new_contact["Title"] = title_id
        if primary_contact_value:
            new_contact["PrimaryContact"] = primary_contact_value
        if owner_ids:
            new_contact["Owners"] = owner_ids
        if notes:
            new_contact["Notes"] = f"<p>{notes}</p>"
        if linkedin_url:
            new_contact["LinkedInURL"] = linkedin_url

        print(f"Creating new contact with data: {new_contact}")

        # Create the contact
        created_contact = api.data.create_entries(contact_entry_type['id'], [new_contact])

        if created_contact:
            print(f"Successfully created contact: {first_name} {last_name}")
            return created_contact[0], "created"
        else:
            print("Failed to create contact - no response from API")
            return None, "failed"

    except Exception as e:
        print(f"An error occurred while creating contact: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, "error"
    
def print_entry_type_info(api: DealCloudAPI, entry_type_name: str):
    """Helper function to print entry type information"""
    entry_types = api.schema.get_entry_types()
    entry_type = next((et for et in entry_types if et['name'] == entry_type_name), None)
    
    if entry_type:
        print(f"\nEntry Type Info for {entry_type_name}:")
        print(f"ID: {entry_type['id']}")
        print(f"API Name: {entry_type['apiName']}")
        print(f"Entry List ID: {entry_type['entryListId']}")
        
        fields = api.schema.get_entry_type_fields(entry_type['id'])
        print("\nFields:")
        for field in fields:
            print(f"- {field['name']} (ID: {field['id']}, API Name: {field['apiName']})")
            if field.get('choiceValues'):
                print("  Choice Values:")
                for choice in field['choiceValues']:
                    print(f"    - {choice['name']} (ID: {choice['id']})")
    else:
        print(f"Entry type {entry_type_name} not found")

    
contact, status = create_contact_with_company(
    api=api,
    first_name="Test",
    last_name="Harty",
    email="Ryanharty15@gmail.com",
    company_name="Test Santé Ventures",
    website="www.santeventures.com",
    job_title="Associate",
    linkedin_url="https://www.linkedin.com/in/ryanharty/",
    notes="Lives in Austin works at Santé Ventures",
    contact_type="Professionals (Non C-Suite)",
    company_type="Service Provider / Business Partner",
    country="United States",
    owner_emails=["ryan.harty@sante.com"],
    primary_contact=True,
)

if status == "existing":
    print("Contact already exists:", contact)
elif status == "created":
    print("New contact created:", contact)
else:
    print(f"Operation failed with status: {status}")
from typing import Dict, List, Optional, Tuple
from dealcloud.api import DealCloudAPI
from dealcloud.utils import get_user_ids_by_email
from fuzzywuzzy import fuzz
import requests
import os
from typing import Tuple, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json


class CompanyType(str, Enum):
    LIMITED_PARTNER = "Limited Partner"
    PORTFOLIO_PROSPECT = "Portfolio Prospect"
    PORTFOLIO_COMPANY = "Portfolio Company"
    HEDGE_FUND = "Hedge Fund"
    VENTURE_CAPITAL = "Venture Capital"
    SERVICE_PROVIDER = "Service Provider / Business Partner"
    ACADEMIC_INSTITUTION = "Academic Institution"
    STRATEGIC = "Strategic"
    FINANCIAL_INSTITUTION = "Financial Institution"
    LAW_FIRM = "Law Firm"
    OTHER = "Other"


class CompanySubType(str, Enum):
    ASSET_MANAGER = "Asset Manager"
    BANK = "Bank"
    INVESTMENT_CONSULTANT = "Investment Consultant"
    ENDOWMENT = "Endowment & Foundation"
    MULTI_FAMILY_OFFICE = "Family Office - Multi"
    SINGLE_FAMILY_OFFICE = "Family Office - Single"
    FUND_MANAGER = "Fund Manager"
    FUND_OF_FUND = "Fund of Fund"
    GOVERNMENT_AGENCY = "Government Agency"
    GROWTH_EQUITY = "Growth Equity"
    HEALTHCARE_SYSTEM = "Healthcare System"
    HNWI = "High-Net-Worth Individual"
    INSURANCE = "Insurance Company"
    INVESTMENT_BANK_LP = "Investment Bank (LP)"
    PE_INVESTOR = "Private Equity Firm (Investor)"
    PRIVATE_PENSION = "Private Sector Pension Fund"
    PUBLIC_PENSION = "Public Pension Fund"
    SOVEREIGN_WEALTH = "Sovereign Wealth Fund"
    WEALTH_MANAGER = "Wealth Manager"
    # Service Provider Types
    ACCELERATOR = "Accelerator"
    ACCOUNTING = "Accounting Firm"
    BANK_SERVICE = "Bank (Service Provider)"
    BUSINESS_BROKER = "Business Broker"
    CONSULTING = "Consulting Firm"
    EXEC_SEARCH = "Executive Search Firm"
    INVESTMENT_BANK = "Investment Bank"
    PE_SERVICE = "Private Equity Firm (Service Provider)"
    VENDOR = "Vendor"


class CompanyCategory(str, Enum):
    HEDGE_FUND = "Hedge Fund"
    PRIVATE_EQUITY = "Private Equity"
    SECONDARY = "Secondary"
    HYBRID = "Hybrid"
    MEDIA_PR = "Media / Public Relations"
    SOFTWARE = "Software"
    ANALYTICS = "Analytics"
    DATA = "Data"
    FACILITIES = "Facilities"
    IT_SECURITY = "IT & Security"
    TRAVEL = "Travel / Hotel / Restaurants"
    UTILITIES = "Utilities"


@dataclass
class CompanyCreateParams:
    """Parameters for creating a company"""
    # Required fields
    company_name: str
    company_type: CompanyType

    # Optional fields
    business_description: Optional[str] = None
    website: Optional[str] = None
    box_folder: Optional[str] = None
    confluence_page: Optional[str] = None
    dashboard_notes: Optional[str] = None
    legacy_company_id: Optional[str] = None
    pitchbook_id: Optional[str] = None
    preferred_pricing: Optional[float] = None

    # Reference fields
    parent_company: Optional[Union[int, str]] = None  # Can be company ID or name
    board_members: Optional[List[Union[int, str]]] = None
    co_investors: Optional[List[Union[int, str]]] = None
    primary_contacts: Optional[List[Union[int, str]]] = None
    sante_contacts: Optional[List[str]] = None  # Email addresses
    sector: Optional[Union[int, str]] = None
    sub_sector: Optional[Union[int, str]] = None

    # Choice fields
    sub_type: Optional[CompanySubType] = None
    category: Optional[CompanyCategory] = None
    is_preferred_vendor: Optional[bool] = None
    secondary_types: Optional[List[CompanyType]] = None

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


def create_company(
        api: DealCloudAPI,
        params: CompanyCreateParams
) -> Tuple[Optional[Dict], str]:
    try:
        company_entry_type = next(
            et for et in api.schema.get_entry_types()
            if et['name'] == 'Company' or et['singularName'] == 'Company'
        )

        # Check if company already exists
        existing_company = find_company_by_name(api, params.company_name)
        if existing_company:
            print(f"Found existing company: {params.company_name}")
            return existing_company, "existing"

        # Get field definitions
        fields = api.schema.get_entry_type_fields(company_entry_type['id'])

        # Create store requests array
        store_requests = []
        entry_id = -1

        def add_field(field_name: str, value: any, ignore_near_dups: bool = True):
            """Helper function to add a field to store_requests"""
            try:
                field = next((f for f in fields if f['apiName'] == field_name), None)
                if not field:
                    print(f"Warning: Field {field_name} not found")
                    return

                if not field.get('isStoreRequestSupported', True) or field.get('isCalculated', False):
                    print(f"Warning: Field {field_name} is not writable")
                    return

                if value is None:
                    return

                print(f"\nProcessing field {field_name}:")
                print(f"Field type: {field['fieldType']}")
                print(f"Value to set: {value}")

                if field['fieldType'] == 2:  # Choice field
                    if isinstance(value, (list, tuple)):
                        # Handle multi-select choice fields
                        choice_values = []
                        for v in value:
                            # Handle enum values
                            if hasattr(v, 'value'):
                                v = v.value
                            print(f"Looking for choice value: {v}")
                            choice_value = next((cv['id'] for cv in field.get('choiceValues', [])
                                                 if cv['name'].lower() == str(v).lower()), None)
                            print(f"Found choice ID: {choice_value}")
                            if choice_value:
                                choice_values.append(choice_value)
                        if choice_values:
                            store_requests.append({
                                "value": choice_values,
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })
                            print(f"Added multi-choice request: {choice_values}")
                    else:
                        # Single choice field
                        # Handle enum values
                        if hasattr(value, 'value'):
                            value = value.value
                        print(f"Looking for single choice value: {value}")
                        print(f"Available choices: {[cv['name'] for cv in field.get('choiceValues', [])]}")
                        choice_value = next((cv['id'] for cv in field.get('choiceValues', [])
                                             if cv['name'].lower() == str(value).lower()), None)
                        print(f"Found choice ID: {choice_value}")
                        if choice_value:
                            store_requests.append({
                                "value": choice_value,
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })
                            print(f"Added single choice request: {choice_value}")
                        else:
                            print(f"Warning: Invalid choice value for {field_name}: {value}")

                elif field['fieldType'] == 5:  # Reference field
                    if isinstance(value, (list, tuple)):
                        ref_ids = []
                        for v in value:
                            ref_id = get_reference_id(api, field, v)
                            if ref_id:
                                ref_ids.append(ref_id)
                        if ref_ids:
                            store_requests.append({
                                "value": ref_ids,
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })
                    else:
                        ref_id = get_reference_id(api, field, value)
                        if ref_id:
                            store_requests.append({
                                "value": ref_id,
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })

                elif field['fieldType'] == 7:  # User field
                    if isinstance(value, (list, tuple)):
                        user_ids = get_user_ids_by_email(api, value)
                        if user_ids:
                            store_requests.append({
                                "value": user_ids,
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })
                    else:
                        user_ids = get_user_ids_by_email(api, [value])
                        if user_ids:
                            store_requests.append({
                                "value": user_ids[0],
                                "ignoreNearDups": ignore_near_dups,
                                "entryId": entry_id,
                                "fieldId": field['id']
                            })
                else:
                    store_requests.append({
                        "value": value,
                        "ignoreNearDups": ignore_near_dups,
                        "entryId": entry_id,
                        "fieldId": field['id']
                    })
                    print(f"Added regular field request: {value}")
            except Exception as e:
                print(f"Warning: Could not add field {field_name}: {str(e)}")
                import traceback
                traceback.print_exc()

        # Add required fields first
        add_field('CompanyName', params.company_name)
        add_field('Type', params.company_type)
        add_field('Database', 'No')  # Required field

        # Optional fields
        add_field('BusinessDescription', params.business_description)
        add_field('Website', params.website)
        add_field('BoxFolder', params.box_folder)
        add_field('ConfluencePage', params.confluence_page)
        add_field('DashboardNotes', params.dashboard_notes)
        add_field('LegacyCompanyID', params.legacy_company_id)
        add_field('PitchBookID', params.pitchbook_id)
        add_field('PreferredPricing', params.preferred_pricing)

        # Reference fields
        add_field('Parent', params.parent_company)
        add_field('BoardMembers', params.board_members)
        add_field('CoInvestors', params.co_investors)
        add_field('PrimaryContacts', params.primary_contacts)
        add_field('SantéContacts', params.sante_contacts)
        add_field('Sector', params.sector)
        add_field('SubSector', params.sub_sector)

        # Choice fields
        add_field('SubType', params.sub_type)
        add_field('Category', params.category)
        add_field('IsPreferredVendor', 'Yes' if params.is_preferred_vendor else None)
        add_field('SecondaryTypes', params.secondary_types)

        if not store_requests:
            print("No valid fields to update")
            return None, "failed"

        print(f"\nFinal store requests: {json.dumps(store_requests, indent=2)}")

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

        # Check for successful creation
        if created_data:
            print(f"\nAPI Response: {json.dumps(created_data, indent=2)}")
            successful_requests = [r for r in created_data if not r.get('error')]
            if successful_requests:
                new_company_id = successful_requests[0]['rowId']
                if new_company_id > 0:  # Valid company ID
                    print(f"Successfully created company: {params.company_name}")
                    company_data = api.data.get_entries(company_entry_type['id'],
                                                        query={"EntryId": new_company_id})
                    if company_data and company_data.get('rows'):
                        return company_data['rows'][0], "created"

        print("Failed to create company - creation was not successful")
        print("Response:", created_data)
        return None, "failed"

    except Exception as e:
        print(f"Error creating company: {str(e)}")
        print("Response content:", getattr(locals().get('response'), 'content', None))
        import traceback
        traceback.print_exc()
        return None, "error"


def get_reference_id(api: DealCloudAPI, field: Dict, value: Union[int, str]) -> Optional[int]:
    """Helper function to get reference ID from either ID or name"""
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        # Logic to find entity by name based on field type
        # This would need to be implemented based on the specific field
        return None
    return None

if __name__ == "__main__":
    from config.settings import DEALCLOUD_CLIENT_ID, DEALCLOUD_CLIENT_SECRET, DEALCLOUD_BASE_URL
    api = DealCloudAPI(client_id=DEALCLOUD_CLIENT_ID, client_secret=DEALCLOUD_CLIENT_SECRET, base_url=DEALCLOUD_BASE_URL)
    # print(find_company_by_name(api, "Santé Ventures"))

    params = CompanyCreateParams(
        company_name="Test Sante ventures",
        company_type=CompanyType.VENTURE_CAPITAL,
        business_description="A test company description",
        website="https://test.com",
        sante_contacts=["ryan.harty@sante.com"],
        sub_type=CompanySubType.FUND_MANAGER,
        category=CompanyCategory.SOFTWARE,
        is_preferred_vendor=True,
        secondary_types=[CompanyType.STRATEGIC, CompanyType.PORTFOLIO_PROSPECT],
        dashboard_notes="Important notes about this company: \n- Key point 1\n- Key point 2"

    )

    result = create_company(api, params)
    print(result)

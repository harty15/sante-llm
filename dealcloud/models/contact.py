from typing import Dict, List, Optional, Tuple
from dealcloud.api import DealCloudAPI
from dealcloud.models.company import create_company
from dealcloud.utils import get_user_ids_by_email, get_country_id, get_title_id
from fuzzywuzzy import fuzz
import requests
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class Salutation(str, Enum):
    MR = "Mr."
    MRS = "Mrs."
    MS = "Ms."
    DR = "Dr."
    PROF = "Prof."


class ContactType(str, Enum):
    LIMITED_PARTNER = "Limited Partner"
    VC_PROFESSIONAL = "Venture Capital Professional"
    HF_PROFESSIONAL = "Hedge Fund Professional"
    INVESTMENT_BANKER = "Investment Banker"
    SERVICE_PROVIDER = "Service Provider"
    CONSULTANT = "Consultant / Advisor / Expert"
    HEALTHCARE_PROFESSIONAL = "Healthcare Professional"
    EXECUTIVE = "Executive / Entrepreneur"
    ASSISTANT = "Assistant"
    ACADEMIC = "Academic"
    STUDENT = "Student / Intern"
    FINANCE_PROFESSIONAL = "Finance Professional"
    SOFTWARE_ENGINEER = "Software Engineer"
    DATA_SCIENTIST = "Data Scientist"
    OTHER = "Other"
    PROFESSIONAL_NON_CSUITE = "Professionals (Non C-Suite)"


class SanteDivision(str, Enum):
    VENTURES = "Santé Ventures"
    CAPITAL = "Santé Capital"
    ENTERPRISE = "Enterprise"


class PeopleFlow(str, Enum):
    TALENT_FIRM = "Talent - Firm"
    TALENT_PORTCO = "Talent - PortCo"
    TALENT_EIR = "Talent - EIR"
    NETWORK = "Network"
    OTHER = "T&N - Other"


@dataclass
class ContactCreateParams:
    """Parameters for creating a contact with all available fields"""
    # Required fields
    first_name: str
    last_name: str

    # Basic Information
    email: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    salutation: Optional[Salutation] = None
    contact_type: Optional[ContactType] = None

    # Additional Contact Info
    other_email: Optional[str] = None
    other_email2: Optional[str] = None
    other_email3: Optional[str] = None
    other_email4: Optional[str] = None
    assistant_email: Optional[str] = None
    assistant_name: Optional[str] = None
    spouse: Optional[str] = None

    # Physical Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    global_postal_code: Optional[str] = None
    country: Optional[Union[str, int]] = None  # Can be name or ID

    # Reference fields
    company_id: Optional[int] = None
    board_memberships: Optional[List[int]] = None
    additional_affiliated_companies: Optional[List[int]] = None
    affiliated_investors: Optional[List[int]] = None
    previous_employment: Optional[List[int]] = None
    connected_to: Optional[List[int]] = None
    conferences_attended: Optional[List[int]] = None
    themes: Optional[List[int]] = None
    sector: Optional[Union[int, str]] = None
    sub_sector: Optional[Union[int, str]] = None

    # Choice fields
    sante_division: Optional[SanteDivision] = None
    people_flow: Optional[PeopleFlow] = None
    contact_frequency: Optional[str] = None  # "30", "60", "90", "180"

    # Boolean flags
    additional_emails: bool = False
    network_expert: bool = False
    talent_prospect: bool = False
    globally_unsubscribed: bool = False
    primary_contact: bool = False

    # Owner Information
    sante_contacts: Optional[List[str]] = None  # List of email addresses

    # File/Document fields
    attachments: Optional[List[Dict]] = None  # List of attachment info
    photo: Optional[bytes] = None  # Binary photo data

    # Administrative
    source_file: Optional[str] = None
    legacy_contact_id: Optional[str] = None
    dc_import_id: Optional[str] = None
    post_go_live_source_file: Optional[str] = None
    dashboard_notes: Optional[str] = None


# Add this helper function to get the title ID
def get_title_id(api: DealCloudAPI, title_name: str) -> Optional[int]:
    """
    Get the ID for a job title
    """
    try:
        # Get the job titles entry type
        titles_entry_type = next(
            et for et in api.schema.get_entry_types()
            if et['name'] == 'Job Title' or et['singularName'] == 'Job Title'
        )

        # Search for the title
        titles = api.data.get_entries(
            titles_entry_type['id'],
            query={"Name": {"$eq": title_name}}
        )

        if titles and titles.get('rows'):
            return titles['rows'][0]['EntryId']

        # If title doesn't exist, create it
        new_title = api.data.create_entries(titles_entry_type['id'], [{
            "EntryId": -1,
            "Name": title_name
        }])

        if new_title:
            return new_title[0]['EntryId']

        return None
    except Exception as e:
        print(f"Error getting/creating title: {str(e)}")
        return None
def create_contact(
        api: DealCloudAPI,
        params: ContactCreateParams
) -> Tuple[Optional[Dict], str]:
    """Creates a new contact with all available fields"""
    try:
        # Get Contact entry type
        contact_entry_type = next(
            et for et in api.schema.get_entry_types()
            if et['name'] == 'Contact' or et['singularName'] == 'Contact'
        )

        # Check for existing contact
        existing_contact = find_contact_by_name_and_email(
            api, params.first_name, params.last_name, params.email
        )
        if existing_contact:
            print(f"Found existing contact: {params.first_name} {params.last_name}")
            return existing_contact, "existing"

        # Get field definitions
        fields = api.schema.get_entry_type_fields(contact_entry_type['id'])
        store_requests = []
        entry_id = -1

        def add_field(field_name: str, value: any, ignore_near_dups: bool = True) -> None:
            """Helper function to add a field to store_requests if writable"""
            try:
                field = next((f for f in fields if f['apiName'] == field_name), None)
                if not field:
                    return

                if not field.get('isStoreRequestSupported', True) or field.get('isCalculated', False):
                    return

                if value is None:
                    return

                print(f"Adding field {field_name} with value {value}")

                if field['fieldType'] == 2:  # Choice field
                    if hasattr(value, 'value'):
                        value = value.value
                    choice_value = next((cv['id'] for cv in field.get('choiceValues', [])
                                         if cv['name'].lower() == str(value).lower()), None)
                    if choice_value:
                        store_requests.append({
                            "value": choice_value,
                            "ignoreNearDups": ignore_near_dups,
                            "entryId": entry_id,
                            "fieldId": field['id']
                        })
                elif field['fieldType'] in [5, 7]:  # Reference or User field
                    store_requests.append({
                        "value": value,
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
            except Exception as e:
                print(f"Warning: Could not add field {field_name}: {str(e)}")

        title_id = None
        if params.job_title:
            title_id = get_title_id(api, params.job_title)
            if not title_id:
                print(f"Warning: Could not find/create title '{params.job_title}'")

        # Add all fields from params
        add_field('FirstName', params.first_name)
        add_field('LastName', params.last_name)
        add_field('Email', params.email)
        add_field('Title', title_id)
        add_field('Department', params.department)
        add_field('LinkedInURL', params.linkedin_url)
        add_field('Notes', f"<p>{params.notes}</p>" if params.notes else None)
        add_field('Salutation', params.salutation)
        add_field('ContactType', params.contact_type)

        # Additional contact info
        add_field('OtherEmail', params.other_email)
        add_field('OtherEmail2', params.other_email2)
        add_field('OtherEmail3', params.other_email3)
        add_field('OtherEmail4', params.other_email4)
        add_field('AssistantEmail', params.assistant_email)
        add_field('AssistantName', params.assistant_name)
        add_field('Spouse', params.spouse)

        # Address fields
        add_field('Address', params.address)
        add_field('City', params.city)
        add_field('State', params.state)
        add_field('GlobalPostalCode', params.global_postal_code)

        if params.country:
            country_id = get_country_id(api, params.country) if isinstance(params.country, str) else params.country
            if country_id:
                add_field('Country', country_id)

        # Reference fields
        if params.company_id:
            add_field('Company', params.company_id)
        if params.board_memberships:
            add_field('BoardMemberships', params.board_memberships)
        if params.additional_affiliated_companies:
            add_field('AdditionalAffliatedCompanies', params.additional_affiliated_companies)
        if params.affiliated_investors:
            add_field('AffiliatedInvestor', params.affiliated_investors)
        if params.previous_employment:
            add_field('PreviousEmployment', params.previous_employment)
        if params.connected_to:
            add_field('ConnectedTo', params.connected_to)
        if params.conferences_attended:
            add_field('ConferencesAttended', params.conferences_attended)
        if params.themes:
            add_field('Themes', params.themes)

        # Choice fields
        add_field('DivisionsAffiliated', params.sante_division)
        add_field('TNProspect', params.people_flow)
        add_field('ContactFrequency', params.contact_frequency)

        # Boolean flags
        add_field('AdditionalEmails', params.additional_emails)
        add_field('NetworkExpert', params.network_expert)
        add_field('TNCandidate', params.talent_prospect)
        add_field('GloballyUnsubscribed', params.globally_unsubscribed)
        add_field('PrimaryContact', 'Yes' if params.primary_contact else None)

        # Owner information
        if params.sante_contacts:
            owner_ids = get_user_ids_by_email(api, params.sante_contacts)
            if owner_ids:
                add_field('Owners', owner_ids)

        # File/Document fields
        if params.attachments:
            add_field('Attachments', params.attachments)
        if params.photo:
            add_field('Photo', params.photo)

        # Administrative fields
        add_field('SourceFile', params.source_file)
        add_field('LegacyContactID', params.legacy_contact_id)
        add_field('DCImport', params.dc_import_id)
        add_field('PostGoLiveSourceFile', params.post_go_live_source_file)
        add_field('DashboardNotes', params.dashboard_notes)
        add_field('Database', 'No')  # Required field

        if not store_requests:
            print("No valid fields to update")
            return None, "failed"

        print(f"\nFinal store requests: {json.dumps(store_requests, indent=2)}")

        # Create the contact
        url = f"{api.token_manager.base_url}/api/rest/v4/data/entrydata/{contact_entry_type['id']}"
        headers = {"Authorization": f"Bearer {api.token_manager.get_valid_token()}"}
        response = requests.post(
            url,
            json={"storeRequests": store_requests},
            headers=headers
        )
        response.raise_for_status()
        created_data = response.json()

        if created_data:
            successful_requests = [r for r in created_data if not r.get('error')]
            if successful_requests:
                new_contact_id = successful_requests[0]['rowId']
                if new_contact_id > 0:
                    print(f"Successfully created contact: {params.first_name} {params.last_name}")
                    contact_data = api.data.get_entries(contact_entry_type['id'],
                                                        query={"EntryId": new_contact_id})
                    if contact_data and contact_data.get('rows'):
                        return contact_data['rows'][0], "created"

        print("Failed to create contact - creation was not successful")
        print("Response:", created_data)
        return None, "failed"

    except Exception as e:
        print(f"Error creating contact: {str(e)}")
        print("Response content:", getattr(locals().get('response'), 'content', None))
        import traceback
        traceback.print_exc()
        return None, "error"


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
) -> Tuple[Optional[Dict], str]:
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


if __name__ == "__main__":
    from config.settings import DEALCLOUD_CLIENT_ID, DEALCLOUD_CLIENT_SECRET, DEALCLOUD_BASE_URL

    api = DealCloudAPI(client_id=DEALCLOUD_CLIENT_ID, client_secret=DEALCLOUD_CLIENT_SECRET,
                       base_url=DEALCLOUD_BASE_URL)

    contact_params = ContactCreateParams(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        job_title="CEO",
        linkedin_url="https://linkedin.com/in/johndoe",
        contact_type=ContactType.EXECUTIVE,
        salutation=Salutation.MR,
        department="Executive",
        notes="Important executive contact",
        sante_division=SanteDivision.VENTURES,
        dashboard_notes="Key strategic contact",
        address="123 Main St",
        city="Austin",
        state="TX",
        country="United States",
        sante_contacts=["ryan.harty@sante.com"],
        primary_contact=True
    )

    result = create_contact(api, contact_params)

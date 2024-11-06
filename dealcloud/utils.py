from typing import Optional, List, Dict
from dealcloud.api import DealCloudAPI
from fuzzywuzzy import fuzz

def get_choice_field_id(api: DealCloudAPI, entry_type_id: int, field_name: str, choice_value: str) -> Optional[int]:
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
    try:
        user_ids = []
        for email in emails:
            users = api.user_management.get_users(email=email)
            if users:
                user_ids.append(users[0]['id'])
        return user_ids
    except Exception as e:
        print(f"Error looking up users by email: {str(e)}")
        return []

def print_entry_type_info(api: DealCloudAPI, entry_type_name: str) -> None:
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
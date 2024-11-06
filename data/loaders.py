import boto3
from io import StringIO
import pandas as pd

def read_latest_csv_from_s3(bucket_name, access_key, secret_key, path='data/'):
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=path)
    csv_files = [obj for obj in response.get('Contents', []) if obj['Key'].endswith('.csv')]
    if not csv_files:
        raise ValueError(f"No CSV files found in {path}")
    latest_file = max(csv_files, key=lambda x: x['LastModified'])
    obj = s3.get_object(Bucket=bucket_name, Key=latest_file['Key'])
    csv_content = obj['Body'].read().decode('utf-8')
    return pd.read_csv(StringIO(csv_content)), latest_file

def load_all_dataframes(bucket_name, aws_access_key_id, aws_secret_access_key):
    # Load all DataFrames
    all_companies, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'all_companies/')
    all_deals, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'all_deals/')
    sante_seen_additional_funding_deals, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'sante_seen_additional_funding_deals/')
    sante_seen_all_companies, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'sante_seen_all_companies/')
    sante_seen_exit_deals, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'sante_seen_exit_deals/')
    meetings_df, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key)
    cap_tables_df, _ = read_latest_csv_from_s3(bucket_name, aws_access_key_id, aws_secret_access_key, 'cap_tables/')

    # Preprocess DataFrames
    meetings_df['companies'] = meetings_df['companies'].apply(lambda x: x.lstrip("['").rstrip("']"))
    meetings_df['types'] = meetings_df['types'].apply(lambda x: x.lstrip("['").rstrip("']").replace("'", ""))
    meetings_df = meetings_df[['page_content', 'title', 'companies', 'types', 'date']]

    cap_tables_df['Company'] = cap_tables_df['Filename'].apply(lambda x: ' '.join(x.split('.')[0].split(' ')[1:-2]))
    cap_tables_df = cap_tables_df[['Company', 'URL', 'Markdown Content']]

    return {
        'all_companies': all_companies,
        'all_deals': all_deals,
        'sante_seen_additional_funding_deals': sante_seen_additional_funding_deals,
        'sante_seen_all_companies': sante_seen_all_companies,
        'sante_seen_exit_deals': sante_seen_exit_deals,
        'meetings_df': meetings_df,
        'cap_tables_df': cap_tables_df
    } 
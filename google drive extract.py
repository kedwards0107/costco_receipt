import io
import os
import os.path
import shutil
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from PyPDF2 import PdfReader
import re
import pandas as pd

#https://www.youtube.com/watch?v=fkWM7A-MxR0&t=1219s(downloaded also)

SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def extract_files(service, folder_name, save_directory):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    response = service.files().list(
        q=f"name = '{folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive'
    ).execute()
    if not response['files']:
        print("No folder found.")
        return None
    folder_id = response['files'][0]['id']
    response = service.files().list(
        q=f"'{folder_id}' in parents"
    ).execute()
    for file in response.get('files', []):
        request = service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Downloaded {file['name']} {int(status.progress() * 100)}%.")
        with open(os.path.join(save_directory, file['name']), 'wb') as f:
            f.write(fh.getbuffer())
    return folder_id

def upload_file_to_drive(service, file_path, folder_id=None):
    file_metadata = {
        'name': os.path.basename(file_path),
        'mimeType': 'text/csv'
    }
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_path, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File ID: {file.get('id')}")

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def extract(text):
    # Regular expression patterns and data extraction logic   
    items_data = re.findall(r'(\d+)([A-Z\s\*]+)([\d.]+) [YN](?:\s*(\d+/\d+\.\d\d)-)?', text.replace('\n', ''))
    
    # items_data = re.findall(r'(\d+)([A-Z\s\*]+)([\d.]+) [YN](?:\s*\d+\/(\d{5}\.\d{2})-)?', text.replace('\n', ''))

    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    date = date_match.group(1) if date_match else "Date not found"
    total_match = re.search(r'TOTAL\s*([\d.]+)', text)
    tax_match = re.search(r'TAX\s*([\d.]+)', text)
    total = total_match.group(1) if total_match else "Total not found"
    items_sold_match = re.search(r'Items Sold: (\d+-?)', text)
    items_sold = items_sold_match.group(1) if items_sold_match else " # Items sold not found"
    
    tax = tax_match.group(1) if tax_match else "Tax not found"
    df = pd.DataFrame(items_data, columns=['Item Code', 'Item', 'Price', 'Discount'])
    df['Date'] = date
    
    #df['Discount'] = df['Discount'].fillna('0.00')
    #df['Discount'] = df['Discount'].apply(lambda x: x[14:] if x else '')
    df['Discount'] = df['Discount'].apply(lambda x: -float(x[14:]) if x else 0.00)
    df = df.append({'Item Code': '', 'Item': 'Total', 'Price': total, 'Discount': '', 'Date': date }, ignore_index=True)
    df = df.append({'Item Code': '', 'Item': 'Tax', 'Price': tax, 'Discount': '', 'Date': date }, ignore_index=True)
    #df = df.append({'Item Code': '', 'Item': 'Items Sold', 'Price': items_sold, 'Discount': '', 'Date': date }, ignore_index=True)
    df = df.append({'Item Code': '', 'Item': (f'Items Sold: {items_sold}'), 'Price': '', 'Discount': '', 'Date': date }, ignore_index=True)
    print([df])
    return df

def main():
    save_directory = "downloaded_files"
    csv_file_name = 'costco_data_output.csv'
    try:
        creds = get_credentials()
        service = build("drive", "v3", credentials=creds)
        folder_id = extract_files(service, "Backupfolder2023", save_directory)

        # Your code for processing PDF files and generating CSV
        all_data_df = pd.DataFrame()
        for file_name in os.listdir(save_directory):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(save_directory, file_name)
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                df = extract(text)
                all_data_df = pd.concat([all_data_df, df], ignore_index=True)
        all_data_df = all_data_df[['Date', 'Item', 'Item Code', 'Price', 'Discount']]
        all_data_df.to_csv(csv_file_name, index=False)

        # Upload the CSV file to the original Google Drive folder
        if folder_id:
            upload_file_to_drive(service, csv_file_name, folder_id)

        csv_file1 = 'costco_data_output.csv'  # Replace with the actual file path of the first CSV
        csv_file2 = 'Dim_costco.csv'  # Replace with the actual file path of the second CSV

        # Read the CSV files into pandas DataFrames
        df1 = pd.read_csv(csv_file1)
        df2 = pd.read_csv(csv_file2)

        # Perform inner join using the "Item Code" column
        combined_df = pd.merge(df1, df2, on='Item Code', how='left')

        # Remove the "Item", "Item Code", and "Discount" columns

        combined_df.loc[combined_df["Item - corrected"].notna(), "Item"] = combined_df["Item - corrected"]
        combined_df.drop(columns=['Item Code', 'Item - corrected'], inplace=True)
        # Rearrange columns in the specified order
        columns_order = ["Date", "Item", "Item Code - corrected", "Item Description", "Amount", "Price", "Discount"]
        combined_df = combined_df[columns_order]
        combined_df.to_csv('combined_file.csv', index=False)
        if folder_id:
            upload_file_to_drive(service, "combined_file.csv", folder_id)

        # Optionally delete local files
        delete_files_in_directory(save_directory)
    except HttpError as e:
        print(e)

if __name__ == '__main__':
    main()




# Display the first few rows of the combined DataFrame
# print(combined_df.head())

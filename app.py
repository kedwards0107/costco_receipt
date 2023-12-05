import os
from PyPDF2 import PdfReader
import re
import pandas as pd

def extract(text):
    # Revised regular expression to include discounts with the new pattern
    items_data = re.findall(r'(\d+)([A-Z\s\*]+)([\d.]+) [YN](?:\s*\w*/\d+([\d.]+)-)?', text.replace('\n', ''))

    # Extracting the date
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    date = date_match.group(1) if date_match else "Date not found"

    # Extracting total and tax
    total_match = re.search(r'TOTAL\s*([\d.]+)', text)
    tax_match = re.search(r'TAX\s*([\d.]+)', text)
    total = total_match.group(1) if total_match else "Total not found"
    tax = tax_match.group(1) if tax_match else "Tax not found"

    # Creating a DataFrame
    df = pd.DataFrame(items_data, columns=['Quantity', 'Item', 'Price', 'Discount'])
    df['Date'] = date
    df['Discount'] = df['Discount'].fillna('0.00')

    # Adding total and tax as new rows
    df = df.append({'Quantity': '', 'Item': 'Total', 'Price': total, 'Discount': '', 'Date': date}, ignore_index=True)
    df = df.append({'Quantity': '', 'Item': 'Tax', 'Price': tax, 'Discount': '', 'Date': date}, ignore_index=True)

    return df

# Initialize an empty DataFrame to store all data
all_data_df = pd.DataFrame()

# Directory containing the PDFs
pdf_dir = 'costcoPDF'

# Loop through each file in the directory
for file_name in os.listdir(pdf_dir):
    if file_name.endswith('.pdf'):
        # Construct the full file path
        file_path = os.path.join(pdf_dir, file_name)
        
        # Read the PDF file
        reader = PdfReader(file_path)
        text = ""

        # Extract text from each page
        for page in reader.pages:
            text += page.extract_text() + "\n"

        # Extract data from the text and append to the main DataFrame
        df = extract(text)
        all_data_df = pd.concat([all_data_df, df], ignore_index=True)

print(all_data_df)

# Reorder DataFrame columns
all_data_df = all_data_df[['Date', 'Item', 'Quantity', 'Price', 'Discount']]

# Export the DataFrame to a CSV file
csv_file_name = 'costco_data_output.csv'
all_data_df.to_csv(csv_file_name, index=False)
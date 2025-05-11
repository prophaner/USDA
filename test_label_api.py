import requests
import json
import pprint

# Load the test data
with open('test_label_request.json', 'r') as f:
    payload = json.load(f)

# Send the request
response = requests.post('http://127.0.0.1:8000/label/', json=payload)

# Print the status code and response
print(f"Status code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    print("\n=== LABEL GENERATION SUCCESSFUL ===")
    
    print("\nDownload Options:")
    print(f"1. PDF Download: {data['pdf_download_url']}")
    print(f"2. PNG Download: {data['png_download_url']}")
    
    print("\nEmbed Code:")
    print("--------------------")
    print(data['embedded_html'])
    print("--------------------")
    
    print("\nUsage Instructions:")
    print("1. To download as PDF: Use the PDF Download URL")
    print("2. To download as PNG: Use the PNG Download URL")
    print("3. To embed in your application: Copy and paste the embed code into your HTML")
else:
    print("\nError Response:")
    pprint.pprint(response.json())
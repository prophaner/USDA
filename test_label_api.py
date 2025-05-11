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
    print(f"\nLabel URL: {data['label_url']}")
    print(f"\nPDF Download URL: {data['pdf_download_url']}")
    print(f"\nPNG Download URL: {data['png_download_url']}")
    
    print("\nEmbedded HTML Code:")
    print("--------------------")
    print(data['embedded_html'])
    print("--------------------")
    
    print("\nLabel Data (partial):")
    print(f"- Recipe Title: {data['label_data']['recipe_title']}")
    print(f"- Label Type: {data['label_data']['label_type']}")
    print(f"- Timestamp: {data['label_data']['timestamp']}")
    print(f"- Number of Ingredients: {len(data['label_data']['recipe_data']['items'])}")
else:
    print("\nError Response:")
    pprint.pprint(response.json())
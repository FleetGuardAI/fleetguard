import urllib.request
import urllib.error
import json

url = 'https://places.googleapis.com/v1/places:autocomplete'
data = json.dumps({
    'input': 'delhi',
    'includedRegionCodes': ['IN'],
    'sessionToken': 'test'
}).encode('utf-8')

req = urllib.request.Request(
    url, 
    data=data, 
    headers={
        'X-Goog-Api-Key': 'fake_key', 
        'Content-Type': 'application/json'
    }
)

try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print(e.read().decode('utf-8'))

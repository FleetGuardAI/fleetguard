import urllib.request
import json
data = json.dumps({"email":"rudra@vahan.in","password":"Rudra@7877"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8000/api/v1/admin/auth/login", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.reason, e.read().decode())

import urllib.request
import urllib.error
import json

url = "http://localhost:8000/api/candidate/session/AD-1MY39T/submit"
req = urllib.request.Request(url, method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Accept", "application/json")

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error Body:", e.read().decode())
except Exception as e:
    print("Exception:", str(e))

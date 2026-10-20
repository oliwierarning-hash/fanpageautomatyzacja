"""Jednorazowo: pobiera refresh token i listuje konta/lokalizacje GBP.

Użycie:
  export GBP_CLIENT_ID=... GBP_CLIENT_SECRET=...
  python3 scripts/gbp_auth.py
Otworzy się przeglądarka z logowaniem Google (konto zarządzające wizytówką).
Typ klienta OAuth w Google Cloud: "Aplikacja komputerowa" (Desktop)."""
import http.server
import os
import urllib.parse
import webbrowser

import requests

CID = os.environ["GBP_CLIENT_ID"]
SECRET = os.environ["GBP_CLIENT_SECRET"]
PORT = 8765
REDIRECT = f"http://localhost:{PORT}"
SCOPE = "https://www.googleapis.com/auth/business.manage"

code_box = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_box["code"] = q.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Gotowe, wróć do terminala.".encode())

    def log_message(self, *a):
        pass


url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": CID, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": SCOPE, "access_type": "offline", "prompt": "consent",
})
server = http.server.HTTPServer(("localhost", PORT), H)
print("Otwieram przeglądarkę...")
webbrowser.open(url)
server.handle_request()

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code_box["code"], "client_id": CID, "client_secret": SECRET,
    "redirect_uri": REDIRECT, "grant_type": "authorization_code",
}, timeout=30).json()
if "refresh_token" not in tok:
    raise SystemExit(f"Brak refresh tokena: {tok}")
h = {"Authorization": f"Bearer {tok['access_token']}"}

print("\nGBP_REFRESH_TOKEN (wpisz do GitHub Secrets, nie wklejaj na czat):")
print(tok["refresh_token"])

accs = requests.get("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=h, timeout=30).json()
for a in accs.get("accounts", []):
    print(f"\nKONTO: {a['name']}  ({a.get('accountName')})")
    locs = requests.get(
        f"https://mybusinessbusinessinformation.googleapis.com/v1/{a['name']}/locations",
        params={"readMask": "name,title"}, headers=h, timeout=30).json()
    for l in locs.get("locations", []):
        print(f"  LOKALIZACJA: {l['name']}  ({l.get('title')})")
print("\nGBP_ACCOUNT_ID = liczba po 'accounts/', GBP_LOCATION_ID = liczba po 'locations/'.")

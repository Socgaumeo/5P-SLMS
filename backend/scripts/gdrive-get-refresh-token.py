"""
One-time script to get Google Drive OAuth2 refresh token.
Run locally, authorize in browser, then copy the refresh token to Railway env vars.

Usage: python3 backend/scripts/gdrive-get-refresh-token.py
"""
import json
import sys
import os

from google_auth_oauthlib.flow import InstalledAppFlow

# Google Drive full access scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    # Find client secret file
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    secret_files = [f for f in os.listdir(project_root) if f.startswith('client_secret') and f.endswith('.json')]

    if not secret_files:
        print("ERROR: No client_secret*.json found in project root")
        sys.exit(1)

    secret_path = os.path.join(project_root, secret_files[0])
    print(f"Using: {secret_files[0]}")

    # Run OAuth flow - opens browser
    flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
    creds = flow.run_local_server(port=8090)

    # Extract tokens
    print("\n" + "=" * 60)
    print("SUCCESS! Copy these to Railway environment variables:")
    print("=" * 60)
    print(f"\nGDRIVE_REFRESH_TOKEN={creds.refresh_token}")
    print(f"GDRIVE_CLIENT_ID={creds.client_id}")
    print(f"GDRIVE_CLIENT_SECRET={creds.client_secret}")
    print("\n" + "=" * 60)

    # Also read project_id from secret file
    with open(secret_path) as f:
        data = json.load(f)
        key = list(data.keys())[0]
        project_id = data[key].get('project_id', '')
        print(f"Google Project: {project_id}")

if __name__ == '__main__':
    main()

import os
from typing import List, Dict, Any, Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Scope for Drive (Read Only) and User Info
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Redirect URI (Must match GCP Console)
REDIRECT_URI = "http://localhost:8000/api/auth/callback"

def get_google_auth_flow():
    """Creates a Google OAuth Flow instance."""
    # In production, use client_secrets.json. For MVP, we can try env vars or a dict.
    # We will assume client configuration is in env vars for simplicity or a file.
    # For this implementation, let's look for a secrets file first, or construct from env.
    
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow

def get_authorization_url():
    """Generates the Google Login URL."""
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return authorization_url, state

def fetch_token(code):
    """Exchanges entry code for an access token."""
    flow = get_google_auth_flow()
    flow.fetch_token(code=code)
    return flow.credentials

def credentials_to_dict(credentials):
    """Converts credentials to a dictionary for session storage."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_credentials_from_dict(cred_dict):
    """Reconstructs credentials from dictionary."""
    return Credentials(
        token=cred_dict.get('token'),
        refresh_token=cred_dict.get('refresh_token'),
        token_uri=cred_dict.get('token_uri'),
        client_id=cred_dict.get('client_id'),
        client_secret=cred_dict.get('client_secret'),
        scopes=cred_dict.get('scopes')
    )

def list_drive_files(credentials) -> List[Dict[str, Any]]:
    """Lists Google Docs files from the user's Drive."""
    service = build('drive', 'v3', credentials=credentials)
    
    # Query for Google Docs only (application/vnd.google-apps.document)
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.document' and trashed=false",
        pageSize=20,
        fields="nextPageToken, files(id, name, modifiedTime, thumbnailLink)"
    ).execute()
    
    items = results.get('files', [])
    return items

def get_doc_content(credentials, file_id: str) -> str:
    """Exports a Google Doc as text."""
    service = build('drive', 'v3', credentials=credentials)
    
    # Export as plain text
    content = service.files().export_media(
        fileId=file_id,
        mimeType='text/plain'
    ).execute()
    
    return content.decode('utf-8')

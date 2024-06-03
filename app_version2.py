import tempfile
import os
import zipfile
import time
from flask import Flask, request, redirect, render_template, send_file
from skimage import io
import base64
import glob
import numpy as np
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import json

app = Flask(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Lee las credenciales desde las variables de entorno
credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if credentials_json:
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
else:
    raise ValueError("No GOOGLE_APPLICATION_CREDENTIALS found in environment variables")

service = build('drive', 'v3', credentials=credentials)

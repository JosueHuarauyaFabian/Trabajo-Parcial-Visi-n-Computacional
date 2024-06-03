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

# IDs de las carpetas en Google Drive
DRIVE_FOLDER_IDS = {
    "Animales": "1LxicGpnR4mwnvb6dDYLqKvFic3ZBCfGg",
    "Frutas": "1yt7IDii7CGhMEBWmZvUnWp0cG2omBAVQ",
    "Vehículos": "1L-SKX7ccMZqFXFFVQxjuYEZ7iZB0m22l",
    "Formas Geométricas": "1KnbPkxwrSl06X9zBsZcmXcUA46Z-wSW2",
    "Objetos de la Casa": "1qHefVFZ5sm0Vgr7VkUnndW1S1SshaF0W"
}

@app.route("/")
def main():
    return render_template("index.html")

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/gallery')
def gallery():
    # Obtener la lista de archivos desde Google Drive
    file_lists = []
    for category, folder_id in DRIVE_FOLDER_IDS.items():
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            spaces='drive',
            fields="files(id, name)").execute()
        files = results.get('files', [])
        file_lists.append((category, files))
    return render_template('gallery.html', file_lists=file_lists)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        category = request.form.get('category')
        object_name = request.form.get('objectName').strip().replace(' ', '_')
        timestamp = int(time.time())
        filename = f"{category}_{object_name}_{timestamp}.png"
        
        # Crear archivo temporal para la imagen
        with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix='.png') as fh:
            fh.write(base64.b64decode(img_data))
            file_path = fh.name

        # Subir archivo a Google Drive
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_IDS[category]]  # ID de la carpeta en Google Drive para la categoría
        }
        media = MediaFileUpload(file_path, mimetype='image/png')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print(f"File ID: {file.get('id')}")
        os.remove(file_path)
        print("Image uploaded to Google Drive")
    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)

@app.route('/uploads/<category>', methods=['GET'])
def list_files(category):
    # Obtener archivos de la carpeta de Google Drive correspondiente a la categoría
    folder_id = DRIVE_FOLDER_IDS.get(category)
    if not folder_id:
        return "Categoría no encontrada", 404
    
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        spaces='drive',
        fields="files(id, name)").execute()
    files = results.get('files', [])

    return render_template('files_list.html', files=files, category=category)

@app.route('/uploads/<category>/<file_id>', methods=['GET'])
def get_file(category, file_id):
    # Descargar el archivo desde Google Drive
    try:
        request = service.files().get_media(fileId=file_id)
        fh = tempfile.NamedTemporaryFile(delete=False)
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.close()
        return send_file(fh.name, mimetype='image/png')
    except Exception as e:
        print(e)
        return "Error retrieving file", 500

@app.route('/download_all', methods=['GET'])
def download_all():
    zip_filename = "images.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for category, folder_id in DRIVE_FOLDER_IDS.items():
            results = service.files().list(
                q=f"'{folder_id}' in parents",
                spaces='drive',
                fields="files(id, name)").execute()
            files = results.get('files', [])
            for file in files:
                request = service.files().get_media(fileId=file['id'])
                fh = tempfile.NamedTemporaryFile(delete=False)
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.close()
                zipf.write(fh.name, f"{category}/{file['name']}")
                os.remove(fh.name)

    return send_file(zip_filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

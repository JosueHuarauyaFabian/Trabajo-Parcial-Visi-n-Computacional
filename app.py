import tempfile
import os
import zipfile
from flask import Flask, request, redirect, render_template, send_file, send_from_directory
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

@app.route("/")
def main():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        category = request.form.get('category')
        print(category)
        category_dir = os.path.join('static', 'uploads', category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=category_dir) as fh:
            fh.write(base64.b64decode(img_data))
        print("Image uploaded")
    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)

@app.route('/uploads/<category>', methods=['GET'])
def list_files(category):
    category_dir = os.path.join('static', 'uploads', category)
    if not os.path.exists(category_dir):
        return "Category not found", 404

    files = os.listdir(category_dir)
    return render_template('files_list.html', files=files, category=category)

@app.route('/uploads/<category>/<filename>', methods=['GET'])
def get_file(category, filename):
    return send_from_directory(os.path.join('static', 'uploads', category), filename)

@app.route('/download_all', methods=['GET'])
def download_all():
    zip_filename = "images.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk('static/uploads'):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), 'static/uploads'))
    
    return send_file(zip_filename, as_attachment=True)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    categories = ["Animales", "Frutas", "Vehiculos", "Formas Geométricas", "Objetos de la Casa"]
    labels = []
    for category in categories:
        filelist = glob.glob(f'static/uploads/{category}/*.png')
        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]
        labels_read = np.array([category] * images_read.shape[0])
        images.append(images_read)
        labels.append(labels_read)
    images = np.vstack(images)
    labels = np.concatenate(labels)
    np.save('X.npy', images)
    np.save('y.npy', labels)
    return "OK!"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file('./X.npy')

@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file('./y.npy')

if __name__ == "__main__":
    categories = ["Animales", "Frutas", "Vehiculos", "Formas Geométricas", "Objetos de la Casa"]
    for category in categories:
        category_dir = os.path.join('static', 'uploads', category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
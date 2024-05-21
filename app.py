import tempfile
import os
from flask import Flask, request, redirect, send_file, render_template
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        category = request.form.get('category')
        print(category)
        if not os.path.exists(category):
            os.makedirs(category)
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=category) as fh:
            fh.write(base64.b64decode(img_data))
        print("Image uploaded")
    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    categories = ["cat1", "cat2", "cat3"]  # replace with your categories
    digits = []
    for category in categories:
        filelist = glob.glob('{}/*.png'.format(category))
        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]
        digits_read = np.array([category] * images_read.shape[0])
        images.append(images_read)
        digits.append(digits_read)
    images = np.vstack(images)
    digits = np.concatenate(digits)
    np.save('X.npy', images)
    np.save('y.npy', digits)
    return "OK!"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file('./X.npy')

@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file('./y.npy')

if __name__ == "__main__":
    app.run(debug=True)

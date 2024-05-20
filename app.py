from flask import Flask, render_template, request
import os
import base64

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_drawing', methods=['POST'])
def save_drawing():
    data = request.form['image']
    category = request.form['category']
    image_data = base64.b64decode(data.split(',')[1])
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, category)):
        os.makedirs(os.path.join(UPLOAD_FOLDER, category))
    filename = f"{UPLOAD_FOLDER}/{category}/{category}_{len(os.listdir(os.path.join(UPLOAD_FOLDER, category)))}.png"
    with open(filename, 'wb') as f:
        f.write(image_data)
    return 'Drawing saved!'

if __name__ == '__main__':
    app.run(debug=True)

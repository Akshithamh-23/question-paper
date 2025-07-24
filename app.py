import os
import zipfile
import hashlib
from flask import Flask, request, send_file, render_template, flash, redirect
from werkzeug.utils import secure_filename
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from PIL import Image
import numpy as np
from utils.steganography import embed_file_in_image
from utils.steg_image import extract_file_from_image

app = Flask(__name__)
app.secret_key = 'secret123'
UPLOAD_FOLDER = 'uploads'
STEGO_FOLDER = 'stego_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STEGO_FOLDER, exist_ok=True)

# ============================
# UTILITY FUNCTIONS
# ============================

def generate_key(faculty_id):
    return hashlib.sha256(faculty_id.encode()).digest()

def encrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        plaintext = f.read()
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    encrypted_data = iv + ciphertext
    encrypted_path = file_path + '.enc'
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_data)
    return encrypted_path

def decrypt_file(encrypted_path, key, original_filename):
    with open(encrypted_path, 'rb') as f:
        data = f.read()
    iv = data[:16]
    ciphertext = data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    decrypted_path = os.path.join(UPLOAD_FOLDER, f'decrypted_{original_filename}')
    with open(decrypted_path, 'wb') as f:
        f.write(plaintext)
    return decrypted_path

def hash_file(file_path):
    sha = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

# ============================
# ROUTES
# ============================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    faculty_id = request.form['faculty_id']
    question_paper = request.files['question_paper']
    if question_paper.filename == '':
        flash('No file selected')
        return redirect('/')

    filename = secure_filename(question_paper.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    question_paper.save(file_path)

    key = generate_key(faculty_id)
    encrypted_path = encrypt_file(file_path, key)
    file_hash = hash_file(file_path)

    zip_filename = os.path.join(UPLOAD_FOLDER, 'encrypted_package.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        zipf.write(encrypted_path, arcname='encrypted_question.enc')
        with open(os.path.join(UPLOAD_FOLDER, 'key.txt'), 'w') as f:
            f.write(faculty_id)
        zipf.write(os.path.join(UPLOAD_FOLDER, 'key.txt'), arcname='key.txt')
        with open(os.path.join(UPLOAD_FOLDER, 'hash.txt'), 'w') as f:
            f.write(file_hash)
        zipf.write(os.path.join(UPLOAD_FOLDER, 'hash.txt'), arcname='hash.txt')
        with open(os.path.join(UPLOAD_FOLDER, 'meta.txt'), 'w') as f:
            f.write(filename)
        zipf.write(os.path.join(UPLOAD_FOLDER, 'meta.txt'), arcname='meta.txt')

    flash('Encryption successful! Download the ZIP file.')
    return send_file(zip_filename, as_attachment=True)

@app.route('/embed', methods=['POST'])
def embed():
    zip_file = request.files['zip_file']
    cover_image = request.files['cover_image']

    if not zip_file or not cover_image:
        flash('Missing ZIP file or image')
        return redirect('/')

    zip_path = os.path.join(UPLOAD_FOLDER, secure_filename(zip_file.filename))
    image_path = os.path.join(UPLOAD_FOLDER, secure_filename(cover_image.filename))
    zip_file.save(zip_path)
    cover_image.save(image_path)

    file_hash = hash_file(zip_path)
    try:
        stego_image_path = embed_file_in_image(zip_path, file_hash, image_path)
    except Exception as e:
        flash(f"Error embedding data: {str(e)}")
        return redirect('/')

    flash('Data embedded successfully!')
    return send_file(stego_image_path, as_attachment=True)

@app.route('/extract', methods=['POST'])
def extract():
    stego_image = request.files['stego_image']

    if not stego_image:
        flash('No stego image uploaded')
        return redirect('/')

    image_path = os.path.join(UPLOAD_FOLDER, secure_filename(stego_image.filename))
    stego_image.save(image_path)

    try:
        zip_path, hash_value = extract_file_from_image(image_path)
        import time
        timestamp = str(int(time.time()))
        extracted_zip_path = os.path.join(UPLOAD_FOLDER, f'extracted_{timestamp}.zip')
        os.rename(zip_path, extracted_zip_path)

        flash('Stego image successfully extracted! Now upload this ZIP and your faculty ID to decrypt.')
        return send_file(extracted_zip_path, as_attachment=True)

    except Exception as e:
        flash(f"Error during extraction: {str(e)}")
        return redirect('/')

@app.route('/decrypt', methods=['POST'])
def decrypt():
    zip_file = request.files['zip_file']
    faculty_id = request.form['faculty_id_decrypt']

    if not zip_file:
        flash('No ZIP file uploaded')
        return redirect('/')

    zip_path = os.path.join(UPLOAD_FOLDER, secure_filename(zip_file.filename))
    zip_file.save(zip_path)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(UPLOAD_FOLDER)

        key = generate_key(faculty_id)
        encrypted_path = os.path.join(UPLOAD_FOLDER, 'encrypted_question.enc')

        meta_path = os.path.join(UPLOAD_FOLDER, 'meta.txt')
        with open(meta_path, 'r') as f:
            original_filename = f.read().strip()

        decrypted_path = decrypt_file(encrypted_path, key, original_filename)

        flash('Decryption successful! Download the file.')
        return send_file(decrypted_path, as_attachment=True)

    except Exception as e:
        flash(f"Error during decryption: {str(e)}")
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
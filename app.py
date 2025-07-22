from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
from werkzeug.utils import secure_filename
from utils.pipeline import encrypt_pipeline
from utils.decryption_pipeline import decrypt_zip_file

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
DECRYPTED_FOLDER = 'decrypted'  # ✅ Added
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'mp3', 'wav', 'zip', 'rar'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)  # ✅ Ensure decrypted folder exists

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    if request.method == 'POST':
        input_file = request.files.get('input_file')
        faculty_id = request.form.get('faculty_id')

        if not input_file or not faculty_id:
            flash("Please provide both faculty ID and a file.")
            return render_template('index.html')

        input_path = os.path.join(UPLOAD_FOLDER, input_file.filename)
        input_file.save(input_path)

        cover_image_path = "static/default_cover.png"
        output_stego_path = "stego_outputs/output.png"

        try:
            success, message, zip_path = encrypt_pipeline(
                input_path, cover_image_path, output_stego_path, faculty_id
            )
        except Exception as e:
            flash(f"Encryption pipeline error: {str(e)}")
            return render_template('index.html')

        if success:
            zip_filename = os.path.basename(zip_path)
            flash("Encryption completed successfully!")
            return render_template('index.html', zip_file=zip_filename)
        else:
            flash(f"Encryption failed: {message}")
            return render_template('index.html')

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join('payload_zip', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found.")
        return redirect(url_for('encrypt'))

from flask import request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from utils.decryption_pipeline import decrypt_zip_file  # ✅ Ensure this import works
from config import UPLOAD_FOLDER

@app.route('/decrypt', methods=['POST'])
def decrypt():
    encrypted_zip = request.files.get('encrypted_zip')
    faculty_id = request.form.get('faculty_id')

    if not encrypted_zip or not faculty_id:
        flash('Please provide both Faculty ID and a ZIP file.')
        return redirect(url_for('index'))

    filename = secure_filename(encrypted_zip.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, filename)
    encrypted_zip.save(zip_path)

    try:
        output_files = decrypt_zip_file(zip_path, faculty_id)
        
        # ✅ Only send base filenames (e.g., "Q1.pdf", not full path)
        file_names = [os.path.basename(f) for f in output_files]

        flash(f"✅ Decryption successful. Extracted {len(file_names)} file(s).")
        return render_template('index.html', decrypted_files=file_names)

    except Exception as e:
        flash(f"❌ Decryption failed: {str(e)}")
        return redirect(url_for('index'))


# ✅ New route to serve decrypted files
from flask import send_from_directory
from config import DECRYPTED_FOLDER

@app.route('/download_decrypted/<filename>')
def download_decrypted_file(filename):
    file_path = os.path.join(DECRYPTED_FOLDER, filename)
    if os.path.exists(file_path):
        return send_from_directory(DECRYPTED_FOLDER, filename, as_attachment=True)
    else:
        flash("Decrypted file not found.")
        return redirect(url_for('index'))






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

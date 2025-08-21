import os
import tempfile
import zipfile
import traceback
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from utils.steg_image import extract_file_from_image  # Make sure this is present
from config import DECRYPTED_FOLDER, UPLOAD_FOLDER

def generate_key(faculty_id):
    return hashlib.sha256(faculty_id.encode()).digest()

def verify_hash(file_path, expected_hash):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash

def decrypt_pipeline(stego_image_path, faculty_id):
    try:
        print("📥 Extracting ZIP from stego image...")
        zip_path, _ = extract_file_from_image(stego_image_path)  # returns ZIP path

        with tempfile.TemporaryDirectory() as tmpdirname:
            print(f"📦 Unzipping to: {tmpdirname}")
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(tmpdirname)

            enc_file = os.path.join(tmpdirname, 'encrypted_question.enc')
            hash_file = os.path.join(tmpdirname, 'hash.txt')
            meta_file = os.path.join(tmpdirname, 'meta.txt')

            # Check all required files are present
            for f in [enc_file, hash_file, meta_file]:
                if not os.path.exists(f):
                    return False, f"Missing required file: {f}", None

            with open(meta_file, 'r') as f:
                original_filename = f.read().strip()

            with open(hash_file, 'r') as f:
                expected_hash = f.read().strip()

            with open(enc_file, 'rb') as f:
                encrypted_data = f.read()

            key = generate_key(faculty_id)
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]

            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

            # Save decrypted file
            os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
            decrypted_file_path = os.path.join(DECRYPTED_FOLDER, f"decrypted_{original_filename}")
            with open(decrypted_file_path, 'wb') as f:
                f.write(decrypted_data)

            # Verify hash
            if not verify_hash(decrypted_file_path, expected_hash):
                return False, "Hash mismatch! File may be tampered with.", None

            print(f"✅ Decrypted file saved: {decrypted_file_path}")
            return True, "Decryption successful.", [f"decrypted_{original_filename}"]

    except Exception as e:
        print("❌ Decryption error:")
        traceback.print_exc()
        return False, f"Decryption failed: {str(e)}", None

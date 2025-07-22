import os
import tempfile
import zipfile
import traceback
from cryptography.fernet import Fernet
from utils.hash_util import calculate_sha256
from utils.conversion import convert_file_format
from config import DECRYPTED_FOLDER, KEY_FOLDER

def decrypt_pipeline(encrypted_zip_path, faculty_id):
    try:
        base_id = os.path.splitext(faculty_id)[0]
        key_path = os.path.join(KEY_FOLDER, f"{base_id}.key")

        print(f"🔑 Looking for key at: {key_path}")
        if not os.path.exists(key_path):
            return False, f"Key file not found: {key_path}", None

        with open(key_path, "rb") as key_file:
            key = key_file.read()
        cipher = Fernet(key)

        decrypted_files = []

        with tempfile.TemporaryDirectory() as tmpdirname:
            print(f"📦 Extracting ZIP to: {tmpdirname}")
            with zipfile.ZipFile(encrypted_zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            for root, _, files in os.walk(tmpdirname):
                for filename in files:
                    if not filename.endswith(".enc"):
                        print(f"⚠️ Skipping non-encrypted file: {filename}")
                        continue

                    enc_file_path = os.path.join(root, filename)
                    try:
                        print(f"🔐 Decrypting file: {enc_file_path}")
                        with open(enc_file_path, "rb") as enc_file:
                            encrypted_data = enc_file.read()

                        decrypted_data = cipher.decrypt(encrypted_data)

                        output_filename = filename.replace(".enc", "")
                        output_path = os.path.join(DECRYPTED_FOLDER, output_filename)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        with open(output_path, "wb") as dec_file:
                            dec_file.write(decrypted_data)

                        convert_file_format(output_path)

                        # ✅ ONLY save the filename, not full path
                        decrypted_files.append(output_filename)

                        print(f"✅ Decrypted and saved: {output_path}")

                    except Exception as file_error:
                        print(f"❌ Decryption failed for {filename}: {str(file_error)}")
                        traceback.print_exc()
                        return False, f"Decryption failed for {filename}: {str(file_error)}", None

        return True, "Decryption successful.", decrypted_files

    except Exception as e:
        print("⚠️ Top-level decryption error:")
        traceback.print_exc()
        return False, f"Error during decryption: {str(e)}", None


def decrypt_zip_file(zip_path, faculty_id):
    success, message, files = decrypt_pipeline(zip_path, faculty_id)
    if not success:
        raise Exception(message)
    return files

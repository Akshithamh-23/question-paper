import cv2
import numpy as np
import os
import tempfile
def extract_file_from_image(stego_image_path):
    image = cv2.imread(stego_image_path)
    if image is None:
        raise ValueError("Stego image not found or invalid.")

    flat_image = image.flatten()

    bits = ''
    for byte in flat_image:
        bits += str(byte & 1)

    # Convert bits to bytes
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte_str = bits[i:i+8]
        if len(byte_str) < 8:
            break
        byte = int(byte_str, 2)
        data.append(byte)

        # Check if we have found the complete marker and some hash data
        if b'||HASH||' in data:
            parts = data.split(b'||HASH||', 1)
            if len(parts) > 1 and len(parts[1]) >= 32:  # Assuming hash is at least 32 chars
                break

    marker = b'||HASH||'
    if marker not in data:
        raise ValueError("Embedded data corrupted or incomplete.")

    zip_data, hash_data = data.split(marker, 1)

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        tmp_zip.write(zip_data)
        zip_path = tmp_zip.name

    return zip_path, hash_data.decode(errors='ignore')

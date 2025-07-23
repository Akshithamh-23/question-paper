import cv2
import numpy as np
import os

def embed_file_in_image(zip_path, file_hash, cover_image_path, output_stego_path=None):
    image = cv2.imread(cover_image_path)
    if image is None:
        raise ValueError("Cover image not found or invalid.")

    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    combined_data = zip_data + b'||HASH||' + file_hash.encode()

    data_bits = ''.join(format(byte, '08b') for byte in combined_data)
    data_len = len(data_bits)

    height, width, channels = image.shape
    capacity = height * width * channels
    if data_len > capacity:
        raise ValueError("Cover image is too small to hold the data.")

    flat_image = image.flatten()

    for i in range(data_len):
        flat_image[i] = (flat_image[i] & 0b11111110) | int(data_bits[i])

    encoded_image = flat_image.reshape(image.shape)

    if output_stego_path is None:
        output_stego_path = os.path.join(
            "stego_images", os.path.basename(zip_path).replace(".zip", "_stego.png")
        )
    os.makedirs(os.path.dirname(output_stego_path), exist_ok=True)
    cv2.imwrite(output_stego_path, encoded_image)
    return output_stego_path

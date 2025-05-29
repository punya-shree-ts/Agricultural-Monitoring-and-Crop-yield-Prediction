import numpy as np
from PIL import Image
import os

def convert_image_to_npz(image_path, output_path):
    # Read the image (assuming 3D RGB image)
    img = Image.open(image_path)
    
    # Convert image to a numpy array (assuming it's RGB)
    data = np.array(img)

    # Create a mask (example: thresholding the image into a binary mask)
    # This can be adjusted to whatever logic you need for the mask
    mask = (data > 128).astype(np.uint8)  # Simple thresholding example

    # Save as .npz file
    np.savez(output_path, data=data, mask=mask)
    print(f"Saved NPZ file to {output_path}")



#convert_image_to_npz(image_path, output_path)

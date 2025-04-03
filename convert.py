import os
import cv2
import numpy as np
import pytesseract

# Set Tesseract path (adjust as needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

current_dir = os.getcwd()
letters_dir = os.path.join(current_dir, "letters")
os.makedirs(letters_dir, exist_ok=True)

folder_path = "scans/"
image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

min_image_size = 10000
letter_contours = []

print(f"Found {len(image_files)} images in {folder_path}")

# Step 1: Collect contours from all images
for file in image_files:
    image_path = os.path.join(folder_path, file)
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ Could not load {file}")
        continue

    print(f"📷 Processing {file}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"➡️ Found {len(contours)} contours in {file}")

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 10 or h < 10:
            continue  # Skip small noise

        letter_crop = image[y:y+h, x:x+w]
        letter_contours.append((x, letter_crop, file))  # Save with X-position

# Step 2: Sort and save the letter crops
print(f"✂️ Total valid contours collected: {len(letter_contours)}")

letter_contours.sort(key=lambda item: item[0])  # Sort left to right

saved_files = 0
for i, (_, letter_crop, source_file) in enumerate(letter_contours):
    temp_file = os.path.join(letters_dir, f"letter_{i}.png")
    cv2.imwrite(temp_file, letter_crop)

    if os.path.getsize(temp_file) >= min_image_size:
        saved_files += 1
    else:
        os.remove(temp_file)

print(f"✅ Saved {saved_files} letter images after filtering small ones.")

# Step 3: OCR & folder sorting
ocr_success = 0
for file in os.listdir(letters_dir):
    if file.endswith(".png"):
        img_path = os.path.join(letters_dir, file)
        img = cv2.imread(img_path)
        detected_text = pytesseract.image_to_string(img, config="--psm 10").strip().upper()

        if len(detected_text) == 1 and detected_text.isalpha():
            ocr_success += 1
            letter_folder = os.path.join(letters_dir, detected_text)
            os.makedirs(letter_folder, exist_ok=True)
            os.rename(img_path, os.path.join(letter_folder, file))

print(f"🔠 OCR success on {ocr_success} letters.")
print("🏁 Letters sorted successfully!")

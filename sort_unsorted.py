"""sort_unsorted.py

Scan "unsorted" folders under `letters/` and try to OCR single-letter crops using
Tesseract. Confident matches are moved into `letters/<LETTER>/`; ambiguous ones
are placed into a `review/` subfolder. Safe to re-run.

Usage:
    python sort_unsorted.py [--source letters/unsorted_magazine_scan3] [--threshold 50] [--sync]

Options:
  --source   Path to an unsorted folder (default: finds folders matching letters/unsorted*)
  --threshold Confidence threshold for accepting OCR results (0-100, default 50).
  --sync     After moving files, sync letters into static folder by calling app.sync_letters_to_static().
  --dry-run  Show what would be done without moving files.
"""

import argparse
import os
import shutil
import pprint
import sys

try:
    import cv2
    import pytesseract
except Exception as e:
    print("Missing dependency:", e)
    print("Install requirements: pip install opencv-python pytesseract")
    sys.exit(1)

# Default tesseract path if available in convert.py
pytesseract.pytesseract.tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', r"C:\Program Files\Tesseract-OCR\tesseract.exe")

VALID_EXTS = ('.png', '.jpg', '.jpeg', '.gif')


def ocr_single_char(path):
    """Try to OCR a single character from the image at `path`.
    Returns (char_or_None, confidence)
    confidence is an int 0-100 (or -1 when unavailable).
    """
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, 0

    # Basic preprocessing: resize small images a bit, threshold
    h, w = img.shape[:2]
    if max(h, w) < 40:
        scale = 2
        img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_LINEAR)

    _, th = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Config: single character, uppercase alphabet
    base_config = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # First try: psm 10 (treat image as single character)
    try:
        text = pytesseract.image_to_string(th, config=f"--psm 10 {base_config}")
    except Exception as e:
        return None, 0

    text = (text or '').strip().upper()
    if len(text) == 1 and text.isalpha():
        # Confidence not provided by image_to_string; try image_to_data for confidence
        data = pytesseract.image_to_data(th, config=f"--psm 10 {base_config}", output_type=pytesseract.Output.DICT)
        confs = [int(x) for x in data.get('conf', []) if x.strip().lstrip('-').isdigit()]
        conf = confs[0] if confs else -1
        return text, conf

    # Fallback: try psm 8 (treat as single word) and image_to_data picking highest-conf char
    data = pytesseract.image_to_data(th, config=f"--psm 8 {base_config}", output_type=pytesseract.Output.DICT)
    best = None
    for i, txt in enumerate(data.get('text', [])):
        if not txt or not txt.strip():
            continue
        t = txt.strip().upper()
        if len(t) == 1 and t.isalpha():
            try:
                conf = int(data.get('conf', [])[i])
            except Exception:
                conf = -1
            if best is None or conf > best[1]:
                best = (t, conf)

    if best:
        return best

    return None, 0


def unique_dest(dst_dir, filename):
    name, ext = os.path.splitext(filename)
    candidate = filename
    i = 1
    while os.path.exists(os.path.join(dst_dir, candidate)):
        candidate = f"{name}_{i}{ext}"
        i += 1
    return os.path.join(dst_dir, candidate)


def process_folder(src_folder, threshold=50, dry_run=False):
    """Process images in src_folder. Returns summary dict."""
    summary = {
        'processed': 0,
        'moved': 0,
        'review': 0,
        'by_letter': {},
    }

    review_dir = os.path.join(src_folder, 'review')
    os.makedirs(review_dir, exist_ok=True)

    for fname in sorted(os.listdir(src_folder)):
        if not fname.lower().endswith(VALID_EXTS):
            continue
        path = os.path.join(src_folder, fname)
        if not os.path.isfile(path):
            continue

        summary['processed'] += 1
        char, conf = ocr_single_char(path)

        if char and (conf is None or conf >= threshold):
            # move to letters/CHAR/
            dest_dir = os.path.join(os.path.dirname(src_folder), char)
            os.makedirs(dest_dir, exist_ok=True)
            dest = unique_dest(dest_dir, fname)
            if not dry_run:
                shutil.move(path, dest)
            summary['moved'] += 1
            summary['by_letter'][char] = summary['by_letter'].get(char, 0) + 1
            print(f"Moved {fname} -> {os.path.relpath(dest)} (char={char},conf={conf})")
        else:
            # ambiguous
            dest = os.path.join(review_dir, fname)
            if not dry_run:
                shutil.move(path, dest)
            summary['review'] += 1
            print(f"Ambiguous {fname} -> review/ (char={char},conf={conf})")

    return summary


def find_unsorted_roots(base='letters'):
    roots = []
    for entry in os.listdir(base):
        path = os.path.join(base, entry)
        if os.path.isdir(path) and entry.lower().startswith('unsorted'):
            roots.append(path)
    return roots


def main():
    parser = argparse.ArgumentParser(description='Sort unsorted letter crops into letter folders using OCR')
    parser.add_argument('--source', help='Unsorted folder to process (default: auto-find unsorted folders)', default=None)
    parser.add_argument('--threshold', type=int, default=50, help='Confidence threshold 0-100 (default 50)')
    parser.add_argument('--sync', action='store_true', help='Sync letters into static after processing (calls app.sync_letters_to_static)')
    parser.add_argument('--dry-run', action='store_true', help='Do not move files, just show actions')
    args = parser.parse_args()

    sources = []
    if args.source:
        if not os.path.isdir(args.source):
            print('Source folder not found:', args.source)
            sys.exit(1)
        sources = [args.source]
    else:
        sources = find_unsorted_roots()

    if not sources:
        print('No unsorted folders found under letters/. Create a folder named `unsorted_*` and put crops there.')
        sys.exit(0)

    grand = {'processed': 0, 'moved': 0, 'review': 0, 'by_letter': {}}
    for s in sources:
        print('\nProcessing', s)
        res = process_folder(s, threshold=args.threshold, dry_run=args.dry_run)
        pprint.pprint(res)
        for k in ['processed', 'moved', 'review']:
            grand[k] += res.get(k, 0)
        for k, v in res.get('by_letter', {}).items():
            grand['by_letter'][k] = grand['by_letter'].get(k, 0) + v

    print('\nSummary:')
    pprint.pprint(grand)

    if args.sync:
        try:
            import app
            app.sync_letters_to_static()
            print('\nSynced letters to static/')
        except Exception as e:
            print('Could not sync to static:', e)


if __name__ == '__main__':
    main()

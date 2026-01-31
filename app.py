import os
import random
import shutil
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, send_file
from werkzeug.utils import secure_filename
# helper to find unsorted folders
from sort_unsorted import find_unsorted_roots

app = Flask(__name__)

# This is where the app looks for the images (directly in the letters folder, not static)
letters_dir = os.path.join(app.root_path, 'letters')

# Ensure there's a copy inside the Flask `static` folder for easy serving via url_for
static_letters_dir = os.path.join(app.root_path, 'static', 'letters')
os.makedirs(static_letters_dir, exist_ok=True)

def sync_letters_to_static(src=letters_dir, dst=static_letters_dir):
    """Copy letter image folders into the project's static folder so they can be
    referenced via url_for('static', filename=...). This is safe to run on startup.
    """
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_dir = os.path.join(dst, rel) if rel != '.' else dst
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                src_file = os.path.join(root, f)
                dst_file = os.path.join(target_dir, f)
                try:
                    # Copy if destination missing or source is newer
                    if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                        shutil.copy2(src_file, dst_file)
                except Exception as e:
                    print(f"Could not copy {src_file} -> {dst_file}: {e}")

# run sync at startup
sync_letters_to_static()

@app.route('/')
def index():
    # This renders the index.html template, which includes the form for user input
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_text():

    user_input = request.form.get('user_input')


    print("User input:", user_input)

    
    if not user_input:
        return "No text input provided", 400  

    
    letter_images = []

    for letter in user_input:
        # Handle space characters explicitly
        if letter == ' ':
            letter_images.append({'type': 'space'})
            continue

        letter_folder = os.path.join(letters_dir, letter.upper())
        print(f"Looking for folder: {letter_folder}")

        # Check if the folder for the letter exists and contains image files
        if os.path.exists(letter_folder):
            images = [f for f in os.listdir(letter_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if images:
                # Select a random image from available letter variants for a more natural look
                selected = random.choice(images)
                # Prefer static URL; url_for works inside request context
                try:
                    image_path = url_for('static', filename=f'letters/{letter.upper()}/{selected}')
                except RuntimeError:
                    # Fallback to absolute static path if url_for is unavailable
                    image_path = f"/static/letters/{letter.upper()}/{selected}"
                letter_images.append({'type': 'image', 'src': image_path})
                print(f"Found image for {letter}: {selected}")
            else:
                print(f"No images found for letter {letter}")
                letter_images.append({'type': 'missing', 'char': letter.upper()})
        else:
            print(f"Folder not found for letter {letter}")
            letter_images.append({'type': 'missing', 'char': letter.upper()})

    # Always use Serif fallback for missing letters
    font_style = 'serif'
    return render_template('process.html', user_input=user_input, letter_images=letter_images, font_style=font_style)


@app.route('/api/render', methods=['POST'])
def api_render():
    """Return JSON describing how to render the provided text as a list of items.
    Each item is a dict with keys: type: 'image'|'space'|'missing', and src/char when applicable.
    """

    data = request.get_json(silent=True) or {}
    user_input = data.get('text') if isinstance(data, dict) else None

    # Also support form-encoded POSTs for compatibility
    if user_input is None:
        user_input = request.form.get('user_input')

    if user_input is None:
        return jsonify({'error': 'No text provided'}), 400

    items = []
    for letter in user_input:
        if letter == ' ':
            items.append({'type': 'space'})
            continue

        letter_folder = os.path.join(letters_dir, letter.upper())

        if os.path.exists(letter_folder):
            images = [f for f in os.listdir(letter_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if images:
                selected = random.choice(images)
                try:
                    image_path = url_for('static', filename=f'letters/{letter.upper()}/{selected}')
                except RuntimeError:
                    image_path = f"/static/letters/{letter.upper()}/{selected}"
                items.append({'type': 'image', 'src': image_path})
            else:
                items.append({'type': 'missing', 'char': letter.upper()})
        else:
            items.append({'type': 'missing', 'char': letter.upper()})

    return jsonify({'input': user_input, 'items': items})


@app.after_request
def add_cache_headers(response):
    """Add long-lived caching headers for letter images served from static or /letters/ paths."""
    try:
        path = request.path
        if path.startswith('/static/letters/') or path.startswith('/letters/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    except Exception:
        pass
    return response


@app.route('/letters/<path:filename>')
def serve_letter_file(filename):
    """Serve letter image files from the letters directory (backward-compatible).

    We keep this route so any older references to `/letters/...` keep working and get
    the same cache headers added by `add_cache_headers`.
    """
    return send_from_directory(os.path.join(app.root_path, 'letters'), filename)


def _find_font_path(preferred_names=('times.ttf', 'times.ttf', 'timesi.ttf', 'timesbd.ttf')):
    """Try to locate a serif TTF on Windows (fallback to default PIL font).
    Returns a font path or None.
    """
    # Common Windows font directory
    font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    try:
        for root, dirs, files in os.walk(font_dir):
            for name in files:
                lname = name.lower()
                if 'times' in lname and lname.endswith('.ttf'):
                    return os.path.join(root, name)
    except Exception:
        pass
    return None


@app.route('/export_png', methods=['POST'])
def export_png():
    """Server-side renderer: compose letter images and text into a PNG and return it."""
    data = request.form or {}
    user_input = data.get('user_input')
    if not user_input:
        return jsonify({'error': 'no text'}), 400

    # Rendering parameters
    target_height = 144  # pixels for high-res PNG
    gap = 8
    padding = 16

    # Build sequence of (type, payload) where type: 'image' -> path, 'text' -> char, 'space'
    seq = []
    letters_root = os.path.join(app.root_path, 'letters')
    for ch in user_input:
        if ch == ' ':
            seq.append(('space', None))
            continue
        if ch.isalpha():
            folder = os.path.join(letters_root, ch.upper())
            if os.path.isdir(folder):
                imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                if imgs:
                    # pick first for determinism
                    seq.append(('image', os.path.join(folder, imgs[0])))
                    continue
        # fallback text for any other or missing letter
        seq.append(('text', ch.upper()))

    # Load images and measure widths
    elements = []
    total_w = padding * 2
    max_h = target_height
    for typ, payload in seq:
        if typ == 'space':
            w = int(target_height * 0.3)  # space width proportion
            elements.append(('space', w, None))
            total_w += w + gap
        elif typ == 'image':
            try:
                im = Image.open(payload).convert('RGBA')
                # resize to target_height keeping aspect
                w = int(im.width * (target_height / im.height))
                im = im.resize((w, target_height), Image.LANCZOS)
                elements.append(('image', w, im))
                total_w += w + gap
            except Exception:
                # on failure fallback to text
                elements.append(('text', 0, payload))
        else:  # text
            # estimate width by drawing with font
            elements.append(('text', 0, payload))
            # width computed later after font size chosen

    # Choose a font for text fallback
    font_path = _find_font_path()
    try:
        if font_path:
            font = ImageFont.truetype(font_path, 100)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Determine text widths and finalize total width
    draw_tmp = ImageDraw.Draw(Image.new('RGBA', (10,10)))
    for i, (typ, w, payload) in enumerate(elements):
        if typ == 'text':
            # try to fit text to the target_height (leave some padding)
            # binary search font size that fits into target_height*0.9
            lo, hi = 6, 800
            best = 12
            while lo <= hi:
                mid = (lo+hi)//2
                try:
                    f = ImageFont.truetype(font_path, mid) if font_path else ImageFont.load_default()
                except Exception:
                    f = ImageFont.load_default()
                bbox = draw_tmp.textbbox((0,0), payload, font=f)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                if th <= int(target_height*0.9):
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            # create the font with best size
            try:
                f = ImageFont.truetype(font_path, best) if font_path else ImageFont.load_default()
            except Exception:
                f = ImageFont.load_default()
            bbox = draw_tmp.textbbox((0,0), payload, font=f)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            elements[i] = ('text', tw, (payload, f, th))
            total_w += tw + gap

    # Create canvas
    img_w = max(1, total_w)
    img_h = max_h + padding*2
    canvas = Image.new('RGBA', (img_w, img_h), (255,255,255,255))
    draw = ImageDraw.Draw(canvas)

    # Paste elements
    x = padding
    y_center = padding + max_h//2
    for typ, w, payload in elements:
        if typ == 'space':
            x += w + gap
            continue
        if typ == 'image':
            im = payload
            y = padding + (max_h - im.height)//2
            canvas.paste(im, (x, y), im)
            x += im.width + gap
        else:  # text payload: (char, font, th)
            ch, fnt, th = payload
            tw, th_actual = draw.textsize(ch, font=fnt)
            # center vertically
            y = y_center - th_actual//2
            # draw a rectangle behind like missing-text style
            rect_h = int(target_height)
            rect_w = tw + 16
            rect_y = padding + (max_h - rect_h)//2
            rect_x = x
            draw.rectangle([rect_x, rect_y, rect_x+rect_w, rect_y+rect_h], fill=(249,249,249,255), outline=(170,170,170,255))
            # draw character centered in rect
            tx = rect_x + (rect_w - tw)//2
            draw.text((tx, y), ch, font=fnt, fill=(170,0,0,255))
            x += rect_w + gap

    # Draw watermark
    watermark = "@madal3ne"
    try:
        wfont = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    except Exception:
        wfont = ImageFont.load_default()
    try:
        bbox = draw.textbbox((0,0), watermark, font=wfont)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = wfont.getsize(watermark)
    wx = img_w - tw - 8
    wy = img_h - th - 6
    draw.text((wx, wy), watermark, font=wfont, fill=(0,0,0,100))

    # Output
    bio = BytesIO()
    canvas.convert('RGB').save(bio, 'PNG')
    bio.seek(0)
    return send_file(bio, mimetype='image/png', as_attachment=False, download_name='ransom_note.png')


def list_review_images(unsorted_folder_name):
    """Return list of filenames under letters/<unsorted_folder_name>/review (sorted)."""
    review_dir = os.path.join(letters_dir, unsorted_folder_name, 'review')
    if not os.path.isdir(review_dir):
        return []
    return sorted([f for f in os.listdir(review_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])


@app.route('/review')
def review():
    """Manual review UI for ambiguous images."""
    roots = find_unsorted_roots()
    # roots are full paths like letters/unsorted_magazine_scan3
    # present friendly names
    roots_short = [os.path.relpath(r, letters_dir) for r in roots]

    # select a source from query param or default to first
    selected = request.args.get('src')
    if not selected and roots_short:
        selected = roots_short[0]

    images = list_review_images(selected) if selected else []

    # Build static URLs for preview
    images_urls = [url_for('static', filename=f"letters/{selected}/review/{fname}") for fname in images]

    return render_template('review.html', roots=roots_short, selected=selected, images=images, images_urls=images_urls)


@app.route('/review/assign', methods=['POST'])
def review_assign():
    """Assign a review image to a letter folder. Expects JSON: {unsorted: 'unsorted_name', filename: '...', letter: 'A'}"""
    data = request.get_json() or {}
    unsorted = data.get('unsorted')
    filename = data.get('filename')
    letter = data.get('letter')

    if not (unsorted and filename and letter):
        return jsonify({'error': 'missing parameters'}), 400

    # sanitize
    filename = secure_filename(filename)
    letter = letter.strip().upper()
    if len(letter) != 1 or not letter.isalpha():
        return jsonify({'error': 'invalid letter'}), 400

    src_path = os.path.join(letters_dir, unsorted, 'review', filename)
    if not os.path.exists(src_path):
        return jsonify({'error': 'file not found', 'file': src_path}), 404

    dst_dir = os.path.join(letters_dir, letter)
    os.makedirs(dst_dir, exist_ok=True)

    # ensure unique name
    dest = os.path.join(dst_dir, filename)
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(dest):
        dest = os.path.join(dst_dir, f"{base}_{i}{ext}")
        i += 1

    try:
        shutil.move(src_path, dest)
        # sync static copy
        sync_letters_to_static()
        static_url = url_for('static', filename=f"letters/{letter}/{os.path.basename(dest)}")
        return jsonify({'ok': True, 'static_url': static_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review/list')
def review_list():
    """Return JSON list of review images for a given unsorted folder (query ?unsorted=...)
    Fallback to first available unsorted root."""
    unsorted = request.args.get('unsorted')
    roots = find_unsorted_roots()
    roots_short = [os.path.relpath(r, letters_dir) for r in roots]
    if not roots_short:
        return jsonify({'images': []})
    if not unsorted:
        unsorted = roots_short[0]

    images = list_review_images(unsorted)
    urls = [url_for('static', filename=f"letters/{unsorted}/review/{fn}") for fn in images]
    return jsonify({'unsorted': unsorted, 'images': images, 'urls': urls})


if __name__ == '__main__':
  
    app.run(debug=True)

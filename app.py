import os
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# This is where the app looks for the images (directly in the letters folder, not static)
letters_dir = os.path.join(app.root_path, 'letters')

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
                image_path = f"letters/{letter.upper()}/{selected}"
                letter_images.append({'type': 'image', 'src': image_path})
                print(f"Found image for {letter}: {selected}")
            else:
                print(f"No images found for letter {letter}")
                letter_images.append({'type': 'missing', 'char': letter.upper()})
        else:
            print(f"Folder not found for letter {letter}")
            letter_images.append({'type': 'missing', 'char': letter.upper()})

    return render_template('process.html', user_input=user_input, letter_images=letter_images)


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
                image_path = f"letters/{letter.upper()}/{selected}"
                items.append({'type': 'image', 'src': image_path})
            else:
                items.append({'type': 'missing', 'char': letter.upper()})
        else:
            items.append({'type': 'missing', 'char': letter.upper()})

    return jsonify({'input': user_input, 'items': items})


if __name__ == '__main__':
  
    app.run(debug=True)

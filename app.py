import os
from flask import Flask, render_template, request

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
        letter_folder = os.path.join(letters_dir, letter.upper())  
        print(f"Looking for folder: {letter_folder}")  

        # Check if the folder for the letter exists
        if os.path.exists(letter_folder):
            images = os.listdir(letter_folder)
            if images:
                # Get the first image in the folder (if any)
                image_path = f"letters/{letter.upper()}/{images[0]}"
                letter_images.append(image_path)
                print(f"Found image for {letter}: {images[0]}") 
            else:
                print(f"No images found for letter {letter}")  
        else:
            print(f"Folder not found for letter {letter}")  

    
    return render_template('process.html', user_input=user_input, letter_images=letter_images)

if __name__ == '__main__':
  
    app.run(debug=True)

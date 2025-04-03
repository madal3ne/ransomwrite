import os

def sort_and_rename_images(letters_dir):
    # Loop through each folder (subfolder) in the letters directory
    for letter_folder in os.listdir(letters_dir):
        letter_folder_path = os.path.join(letters_dir, letter_folder)
        
        # Only process if it's a directory (i.e., a letter folder like A, B, C, etc.)
        if os.path.isdir(letter_folder_path):
            print(f"Sorting images in: {letter_folder_path}")
            
            # Get all the image files in the current letter folder
            images = [f for f in os.listdir(letter_folder_path) if f.endswith(".png")]
            
            # Sort the images to make sure they're in the correct order
            images.sort() 
            
            # Loop through the images and rename them
            for idx, image in enumerate(images, start=1):
                old_image_path = os.path.join(letter_folder_path, image)
                
                # Create the new image name (e.g., a1.png, b1.png, etc.)
                new_image_name = f"{letter_folder.lower()}{idx}.png"
                new_image_path = os.path.join(letter_folder_path, new_image_name)
                
                # Rename the image
                os.rename(old_image_path, new_image_path)
                print(f"Renamed {image} to {new_image_name}")

letters_dir = "letters" 
sort_and_rename_images(letters_dir)

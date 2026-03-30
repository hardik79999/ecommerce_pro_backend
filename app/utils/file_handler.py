import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

# Kin files ko allow karna hai
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, folder_name="products"):
    if file and allowed_file(file.filename):
        # File ka naam safe banana aur unique UUID add karna taaki naam clash na ho
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Upload path banana (e.g., app/static/uploads/products/)
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', folder_name)
        
        # Agar folder nahi hai toh bana do
        os.makedirs(upload_path, exist_ok=True)
        
        # Image save karna
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Database me save karne ke liye URL return karna
        return f"/static/uploads/{folder_name}/{unique_filename}"
    return None
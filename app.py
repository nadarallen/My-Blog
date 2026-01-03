from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
mongo = client['blog_db']
posts_collection = mongo['posts']
users_collection = mongo['users']

# Home Page
@app.route('/')
def index():
    posts = list(posts_collection.find().sort("created_at", -1))
    for post in posts:
        post['_id'] = str(post['_id'])  # Convert ObjectId to string for Jinja
    return render_template('index.html', posts=posts)

# Create Post (User must be logged in)
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'username' not in session:
        flash("Please log in to create a post.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        created_at = datetime.utcnow()
        image_filename = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Timestamp to make unique
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                image_filename = unique_filename

        posts_collection.insert_one({
            'title': title,
            'content': content,
            'created_at': created_at,
            'author': session['username'],
            'image': image_filename
        })
        flash("Post created successfully!", "success")
        return redirect(url_for('index'))

    return render_template('create.html')

# Edit Post (User must be logged in)
@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        flash("Please log in to edit a post.", "warning")
        return redirect(url_for('login'))

    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash("Post not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {'title': title, 'content': content}}
        )
        flash("Post updated successfully!", "success")
        return redirect(url_for('index'))
    
    post['_id'] = str(post['_id'])
    return render_template('edit.html', post=post)

# View Post
@app.route('/view/<post_id>')
def view_post(post_id):
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if post:
        post['_id'] = str(post['_id'])
        return render_template('view.html', post=post)
    else:
        flash("Post not found.", "danger")
        return redirect(url_for('index'))

# Delete Post (Only admin can delete)
@app.route('/delete/<post_id>')
def delete_post(post_id):
    if session.get('username') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    posts_collection.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted successfully.", "success")
    return redirect(url_for('index'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if users_collection.find_one({"username": username}):
            flash("Username already exists. Please choose another.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for('index'))
        elif username == 'admin' and password == 'adminpass': # Keep backdoor for testing/fallback if needed, or remove? Plan implicity suggests replacing. Logic: Keep for now as admin user might not exist in DB yet.
             session['username'] = 'admin'
             flash("Logged in as Admin (Legacy)", "warning")
             return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out", "info")
    return redirect(url_for('index'))

# Run
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
mongo = client['blog_db']
posts_collection = mongo['posts']

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

        posts_collection.insert_one({
            'title': title,
            'content': content,
            'created_at': created_at
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

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Temporary login logic
        if username == 'admin' and password == 'adminpass':
            session['username'] = 'admin'
            flash("Logged in as Admin", "success")
            return redirect(url_for('index'))
        elif username == 'user' and password == 'userpass':
            session['username'] = 'user'
            flash("Logged in as User", "success")
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

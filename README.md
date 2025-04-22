# My Blog

This is a simple blog application built using Python with Flask, MongoDB, and basic frontend technologies. The blog allows users to create, read, update, and delete blog posts. It is designed with a clean, simple interface and utilizes a MongoDB database to store the blog content.

## Tech Stack

- **Backend**: Python with Flask web framework
- **Database**: MongoDB accessed via PyMongo
- **Frontend**: HTML templates rendered with Jinja2, styled with CSS
- **Additional Libraries**: 
  - `Requests` for handling HTTP requests

## Features

- Create, edit, and delete blog posts
- Display blog posts with options to view, update, or delete
- Simple user interface using HTML and CSS
- Data stored in a MongoDB database

## Setup Instructions

1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/nadarallen/My-Blog.git
2. Navigate into the project directory:
    ```bash
    cd My-Blog
3. Install the necessary Python libraries:
    ```bash
    pip install -r requirements.txt
4. Set up your MongoDB database:
 - You need to have MongoDB installed and running. Alternatively, you can use a MongoDB Atlas cluster.
 - Update the database connection URL in the app.py file (where Flask app is initialized).
5. Run the app
   ```bash
   python app.py
6. Visit http://127.0.0.1:5000/ in your web browser to access the blog.

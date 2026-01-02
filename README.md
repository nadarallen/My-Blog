# My Blog

This is a simple blog application built using Python with Flask, MongoDB, and basic frontend technologies. The blog allows users to create, read, update, and delete blog posts. It is designed with a clean, simple interface and utilizes a MongoDB database to store the blog content.

## Tech Stack

- **Backend**: Python with Flask web framework
- **Database**: MongoDB accessed via PyMongo
- **Frontend**: HTML templates rendered with Jinja2, styled with Bootstrap 5
- **Dependencies**:
  - `Flask` for the web framework
  - `pymongo` for MongoDB interaction

## Features

- **User Authentication**: Simple login/logout system (Hardcoded credentials).
- **CRUD Operations**:
  - **Create**: Logged-in users can create new posts.
  - **Read**: View all posts on the homepage or detailed view of a single post.
  - **Update**: Logged-in users can edit posts.
  - **Delete**: Admin users can delete posts.

## Prerequisites

- **Python 3.x**
- **MongoDB**: You need to have MongoDB installed and running locally on port `27017`.

## Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/nadarallen/My-Blog.git
   cd My-Blog
   ```

2. **Install Dependencies**:

   ```bash
   pip install flask pymongo
   ```

   *Note: You can also install from `requirements.txt` if available.*

3. **Start MongoDB**:
   Ensure your local MongoDB instance is running.

4. **Run the Application**:

   ```bash
   python app.py
   ```

5. **Access the Blog**:
   Open your browser and visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

## Authentication

The application uses hardcoded credentials for demonstration purposes:

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `adminpass` | Create, Edit, Delete |
| **User** | `user` | `userpass` | Create, Edit |

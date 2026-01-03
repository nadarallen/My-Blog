# My Blog (Doodle Edition)

A black-and-white, doodle-themed blog application built with Python (Flask) and MongoDB. This project features secure user authentication, image attachments, and a unique hand-drawn aesthetic.

## Tech Stack

- **Backend**: Python, Flask
- **Database**: MongoDB (via PyMongo)
- **Security**: Werkzeug (Password Hashing)
- **Frontend**: HTML5, CSS3 (Custom Doodle Theme), Bootstrap 5 (Grid)
- **Fonts**: 'Patrick Hand' (Headers), 'Outfit' (Body)

## Features

- **User Authentication**:
  - Secure Registration & Login.
  - Password hashing with `scrypt`.
- **CRUD Operations**:
  - **Create**: Authenticated users can write posts and attach images.
  - **Read**: View all posts on the feed or individually.
  - **Update**: Edit post content and update attached images.
  - **Delete**: Admin-only feature.
- **Photo Attachments**: Upload and display images with posts.
- **Unique UI**: Custom "Black & White Doodle" theme with sketchy borders and generated background patterns.

## Prerequisites

- **Python 3.x**
- **MongoDB**: Local instance running on port `27017`.

## Setup Instructions

1. **Clone the repository**:

    ```bash
    git clone https://github.com/nadarallen/My-Blog.git
    cd My-Blog
    ```

2. **Install Dependencies**:

    ```bash
    pip install flask pymongo werkzeug
    ```

    *(Or use `pip install -r requirements.txt`)*

3. **Start MongoDB**:
    Ensure your local MongoDB instance is running.

4. **Run the Application**:

    ```bash
    python app.py
    ```

    The application will automatically create the `static/uploads` directory if it doesn't exist.

5. **Access the Blog**:
    Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.

## Default Credentials

Create your own account via the **Register** page!
*(Legacy `admin`/`adminpass` login is still available for testing purposes)*.

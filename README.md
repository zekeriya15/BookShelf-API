# BookShelf API

A simple Flask RESTful API for managing your reading list, including book details and cover images.

## Requirements

* Python 3.8+
* MySQL Server

## Quick Setup & Run

Follow these steps to get your BookShelf API operational.

### 1. Database Preparation (MySQL)

1.  **Ensure your MySQL server is running.**
2.  **Create the `bookshelf` database:**
    Log in to your MySQL server (e.g., as `root` user) and execute:
    ```sql
    CREATE DATABASE bookshelf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ```

### 2. Project Setup

1.  **Get the Project Files:**
    Download or clone this project to your local machine. Navigate into the project's root directory in your terminal.

2.  **Create & Activate Virtual Environment: (optional)**
    ```bash
    python -m venv myenv
    # Windows: myenv\Scripts\activate
    # macOS/Linux: source myenv/bin/activate
    ```

3.  **Install Python Dependencies:**
    Create a `requirements.txt` file in your project root with the following content:
    ```
    Flask
    Flask-SQLAlchemy
    Flask-Cors
    PyMySQL
    python-dotenv
    ```
    Then, install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure `.env` File:**
    In the project root, create a file named `.env` and add your MySQL connection details.
    **Example `.env` content (based on your screenshot):**
    ```
    MYSQL_USER=root
    MYSQL_PASSWORD= # Leave empty if your root user has no password
    MYSQL_HOST=localhost
    MYSQL_PORT=3306
    MYSQL_DB=bookshelf
    ```
    **Remember to add `.env` to your `.gitignore`!**

### 3. Run the API

With your virtual environment active and `.env` configured, run the Flask application.

* **Using Flask CLI (Recommended for Development):**
    ```bash
    # Windows Command Prompt:
    flask --app main run
    # or
    $env:FLASK_APP="main.py"
    flask run

    # Windows PowerShell:
    $env:FLASK_APP="main.py"
    flask run

    # macOS/Linux:
    export FLASK_APP=main.py
    flask run
    ```
    This will start the development server, usually on `http://127.0.0.1:5000/`.

* **Running the Python file directly:**
    ```bash
    python main.py
    ```

Your application will connect to the MySQL database and create the necessary tables (`reading`) if they don't already exist.

## API Endpoints

Refer to the `main.py` file for a detailed list of all API routes and their HTTP methods (GET, POST, PUT, PATCH, DELETE).

## Project Structure

```
BookShelf-API/
├── .env
├── .gitignore
├── main.py
├── requirements.txt
└── static/
    └── uploads/ (for uploaded images)
```

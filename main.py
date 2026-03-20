from flask import Flask, request, jsonify
import sqlite3
import secrets
import os
from functools import wraps

app = Flask(__name__)


# --- 1. Database Connection Helper ---
def get_db_connection():
    # This automatically finds the database in the same folder as this script, 
    # fixing the PythonAnywhere path issue instantly!
    db_path = os.path.join(os.path.dirname(__file__), 'books.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# --- 2. Authentication Setup ---
def check_auth(username, password):
    return secrets.compare_digest(username, "admin") and secrets.compare_digest(password, "leeds2026")


def authenticate():
    return jsonify({"message": "Unauthorised. Correct credentials required."}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# --- 3. CRUD Endpoints ---
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Book API!"})


# READ: Get a list of books
@app.route("/books", methods=["GET"])
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT bookID, title, authors, average_rating FROM books LIMIT 10').fetchall()
    conn.close()
    return jsonify([dict(book) for book in books])


# CREATE: Add a new book
@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO books (bookID, title, authors, average_rating) VALUES (?, ?, ?, ?)',
                     (data['bookID'], data['title'], data['authors'], data['average_rating']))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"detail": "Book ID already exists"}), 400
    conn.close()
    return jsonify({"message": "Book added successfully!"}), 201


# UPDATE: Change a book's rating
@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.execute('UPDATE books SET average_rating = ? WHERE bookID = ?', (data['average_rating'], book_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({"detail": "Book not found"}), 404
    return jsonify({"message": f"Book {book_id} updated successfully"})


# DELETE: Remove a book (SECURED)
@app.route("/books/<int:book_id>", methods=["DELETE"])
@requires_auth
def delete_book(book_id):
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM books WHERE bookID = ?', (book_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({"detail": "Book not found"}), 404
    return jsonify({"message": f"Book {book_id} deleted successfully by admin"})

if __name__ == '__main__':
    app.run(debug=True)
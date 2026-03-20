from flask import Flask, request, jsonify
from flasgger import Swagger
import sqlite3
import secrets
import os
from functools import wraps

app = Flask(__name__)
# Initialize Swagger UI
swagger = Swagger(app)

# --- Database & Auth Helpers ---
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'books.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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

# --- Endpoints ---

@app.route("/", methods=["GET"])
def home():
    """
    Root Endpoint
    ---
    responses:
      200:
        description: Welcome message
    """
    return jsonify({"message": "Welcome to the Book API!"})

@app.route("/books", methods=["GET"])
def get_books():
    """
    Get a list of books
    ---
    responses:
      200:
        description: Returns a list of up to 10 books
    """
    conn = get_db_connection()
    books = conn.execute('SELECT bookID, title, authors, average_rating FROM books LIMIT 10').fetchall()
    conn.close()
    return jsonify([dict(book) for book in books])

@app.route("/books", methods=["POST"])
def add_book():
    """
    Create a new book
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            bookID:
              type: integer
            title:
              type: string
            authors:
              type: string
            average_rating:
              type: number
    responses:
      201:
        description: Book added successfully
      400:
        description: Book ID already exists
    """
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

@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    """
    Update a book's rating
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            average_rating:
              type: number
    responses:
      200:
        description: Book updated successfully
      404:
        description: Book not found
    """
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.execute('UPDATE books SET average_rating = ? WHERE bookID = ?', (data['average_rating'], book_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({"detail": "Book not found"}), 404
    return jsonify({"message": f"Book {book_id} updated successfully"})

@app.route("/books/<int:book_id>", methods=["DELETE"])
@requires_auth
def delete_book(book_id):
    """
    Delete a book (Requires Admin Basic Auth)
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Book deleted successfully
      401:
        description: Unauthorised
      404:
        description: Book not found
    """
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
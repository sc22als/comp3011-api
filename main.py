from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import sqlite3
import secrets

app = FastAPI(
    title="Goodreads Book API",
    description="Coursework 1 API for Book Data",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Book API!"}


# --- 1. Authentication Setup ---
# This tells FastAPI we are using Basic HTTP Authentication
security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    This function checks if the user has provided the correct login details.
    We use 'secrets.compare_digest' to securely check the strings.
    """
    is_correct_username = secrets.compare_digest(credentials.username, "admin")
    is_correct_password = secrets.compare_digest(credentials.password, "leeds2026")
    
    if not (is_correct_username and is_correct_password):
        # If the details are wrong, we return a 401 Unauthorised error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --- 2. Database Connection Helper ---
def get_db_connection():
    """Opens a connection to the SQLite database and allows column name access."""
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row 
    return conn


# --- 3. Data Models ---
class BookCreate(BaseModel):
    bookID: int
    title: str
    authors: str
    average_rating: float


class BookUpdate(BaseModel):
    average_rating: float


# --- 4. CRUD Endpoints ---
# READ: Get a list of books (Open to everyone)
@app.get("/books")
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT bookID, title, authors, average_rating FROM books LIMIT 10').fetchall()
    conn.close()
    return [dict(book) for book in books]


# CREATE: Add a new book (Open to everyone for now)
@app.post("/books", status_code=201)
def add_book(book: BookCreate):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO books (bookID, title, authors, average_rating) VALUES (?, ?, ?, ?)',
                     (book.bookID, book.title, book.authors, book.average_rating))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Book ID already exists")
    conn.close()
    return {"message": "Book added successfully!"}


# UPDATE: Change a book's rating (Open to everyone)
@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookUpdate):
    conn = get_db_connection()
    cursor = conn.execute('UPDATE books SET average_rating = ? WHERE bookID = ?', (book.average_rating, book_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": f"Book {book_id} updated successfully"}


# DELETE: Remove a book (SECURED: Only 'admin' can do this)
@app.delete("/books/{book_id}")
def delete_book(book_id: int, username: str = Depends(verify_credentials)):
    """
    Notice the 'Depends(verify_credentials)' above. 
    FastAPI will pause the request, check the login details, 
    and only run this code if the user is authorised.
    """
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM books WHERE bookID = ?', (book_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": f"Book {book_id} deleted successfully by {username}"}
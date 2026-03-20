from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="Goodreads Book API",
    description="Coursework 1 API for Book Data",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Book API!"}


# --- 1. Database Connection Helper ---
def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row # Allows us to access columns by name
    return conn


# --- 2. Data Models (Shows clean architecture!) ---
class BookCreate(BaseModel):
    bookID: int
    title: str
    authors: str
    average_rating: float


class BookUpdate(BaseModel):
    average_rating: float


# --- 3. CRUD Endpoints ---
# READ: Get a list of books
@app.get("/books")
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT bookID, title, authors, average_rating FROM books LIMIT 10').fetchall()
    conn.close()
    return [dict(book) for book in books]


# CREATE: Add a new book
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


# UPDATE: Change a book's rating
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


# DELETE: Remove a book
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM books WHERE bookID = ?', (book_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": f"Book {book_id} deleted successfully"}
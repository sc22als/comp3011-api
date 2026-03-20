from fastapi import FastAPI
import sqlite3

app = FastAPI(
    title="Goodreads Book API",
    description="Coursework 1 API for Book Data",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Book API!"}
import sqlite3
import csv

# Connect to (or create) the database file
conn = sqlite3.connect('books.db')
cursor = conn.cursor()

# Create a table (if it does not already exist)
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    bookID INTEGER,
    title TEXT,
    authors TEXT,
    average_rating REAL,
    isbn TEXT,
    isbn13 TEXT,
    language_code TEXT,
    num_pages INTEGER,
    ratings_count INTEGER,
    text_reviews_count INTEGER,
    publication_date TEXT,
    publisher TEXT
)
''')

# Open the CSV file
with open('books.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    # Skip the header row (column names)
    next(reader)
    
    # Counter to track number of rows inserted
    count = 0
    
    # Loop through rows in the CSV
    for row in reader:
        if count >= 100:
            break  # Stop after 100 rows
        
        # Insert row into the table
        cursor.execute('''
        INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
        
        count += 1

# Save changes to the database
conn.commit()

# Close the connection
conn.close()

print("First 100 rows have been imported into books.db")
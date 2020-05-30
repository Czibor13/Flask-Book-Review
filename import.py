import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Initialize databases
db.execute("CREATE TABLE users (username VARCHAR PRIMARY KEY, password VARCHAR NOT NULL)")
db.execute("CREATE TABLE books (isbn VARCHAR (13) PRIMARY KEY, title TEXT NOT NULL, author VARCHAR NOT NULL, year SMALLINT NOT NULL)")
db.execute("CREATE TABLE reviews (id serial PRIMARY KEY, isbn VARCHAR (13) NOT NULL REFERENCES books, username VARCHAR NOT NULL REFERENCES users, review text NOT NULL, rating SMALLINT NOT NULL, UNIQUE (isbn, username))")

# Open the book file
with open("books.csv", 'r', newline='\n') as f:
    # create a csv.reader object
    lines = csv.reader(f, delimiter=',', quotechar='"')
    # Skip the header
    next(lines)
    # Add each book to the database
    for book in lines:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
                    {"isbn": book[0], "title": book[1], "author": book[2], "year": int(book[3])})

# Update the database with the new tables and books
db.commit()

# Print a message when done
print("Finished setting up database.")
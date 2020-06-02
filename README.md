# Flask Book Review


## Prerequisites

Python 3.6+ with the following packages:
```
Flask
Flask-Session
psycopg2-binary
SQLAlchemy
requests
```

## Files

### Root
```
application.py (The main Flask application)
import.py (Sets up PostgreSQL tables, and imports from books.csv)
books.csv (Contains information for 5000 books)
requirements.txt (Lists the python packages that are needed)
readme.md (This file)
```

### Templates
```
books.html (Contains a form for searching for books)
books-add.html (Contains a form for adding books to the database)
book-search.html (Displays search results from books.html form)
error.html (Displays an error message)
index.html (Homepage for the website that shows recent reviews)
isbn.html (Displays reviews and goodreads data for books by isbn)
layout.html (The layout that every other template inherits)
login.html (Contains a form for logging into the site)
register.html (Contains a form for registering on the site)
user.html (A profile page that shows the user's reviews)
```

### /Static/CSS
```
style.css (Local CSS file to provide some changes to bootstrap 4)
style.scss (Sass file that style.css was compiled from)
style.css.map (Map provided by Sass compiler)
```

## Installing

Needs to be run in an enviornment with the following variables set:
```
FLASK_APP (set to application.py)
DATABASE_URL (Url with information for a PostgreSQL)
GOODREADS_API_KEY (A developer api key from https://www.goodreads.com/api/keys)
```

Once the variables are set the server can be started with:
```
flask run
```

Additionally, there is code contained in import.py to construct the tables in the PostgreSQL database, and also to set up the database with information contained in books.csv.
It must be run with the enviornment variable DATABASE_URL

## Author
* Ryne Czibor

## Project1
This project is based on [Project one of CS50 Web Programming with Python and JavaScript](https://docs.cs50.net/web/2018/x/projects/1/project1.html)

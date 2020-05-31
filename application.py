import os, requests

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Check for environment variables
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

if not os.getenv("GOODREADS_API_KEY"):
    raise RuntimeError("GOODREADS_API_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Returns Homepage
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Attempts to register the user based on the information given in the register form
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
        db.commit()
        return render_template("register.html", success=True)
    # Returns a page for users to register, or redirects to the index if logged in
    else: #if request.method == "GET":
        if "user" in session:
            # Already Logged in
            return redirect(url_for("index"))
        # Not logged in currently
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Attempts to log in the user based on the information given in the login form
    if request.method =="POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")

        # Check if there is a matching username and password combo
        if db.execute("SELECT username FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 1:
            # Log user in with the username
            session["user"] = username
            return render_template("login.html", message="You have logged in", success=True)
        else:
            # The information given was not a match
            return render_template("login.html", message="Invalid Credientials", failed=True)

    # Returns a page for users to log in, or redirects to the index if logged in
    else: #if request.method == "GET":
        if "user" in session:
            # Already Logged in
            return redirect(url_for("index"))
        # Not logged in currently
        return render_template("login.html")

# Logs the user out
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# Displays page that allows searching for books.
# Points to /books/search with results
@app.route("/books")
def books():
    return render_template("books.html")

# Takes in ISBN, Author, and Title from /books form and queries the database for each non empty search term
@app.route("/books/search", methods=["POST"])
def book_search():
    # Variable from the form in books.html (could be None)
    isbn = request.form.get("ISBN")
    author = request.form.get("author")
    title = request.form.get("title")

    # This variable is the string part of the query that will be added to
    query = "SELECT * FROM books WHERE"
    # This dictionary is the query input dictionary that is used when sanitizing inputs
    query_dict = {}
    # This list will be joined together to add only the variables with values to the query
    query_parts = []

    # For each variable, check if the variable has a value. If there is a value, add wildcards, and then add it to the query
    if isbn:
        isbn = '%{}%'.format(isbn)
        query_parts.append("isbn LIKE :isbn")
        query_dict["isbn"] = isbn
    if author:
        author = '%{}%'.format(author)
        query_parts.append("author LIKE :author")
        query_dict["author"] = author
    if title:
        title = '%{}%'.format(title)
        query_parts.append("title LIKE :title")
        query_dict["title"] = title

    # If all the variables are None, display a message telling the user they need to specify at least 1 value
    if not query_parts:
        return render_template("book-search.html", message="Please use at least one search term", failed=True)
    
    # Construct the final query string
    query_end = " AND ".join(query_parts)
    query = query + " " + query_end

    # Store the query results
    books = db.execute(query, query_dict).fetchall()

    # If no books were found in the query, let the user know
    if not books:
        return render_template("book-search.html", message="No books were found for your search terms", failed=True)
    
    # Display books found in query
    return render_template("book-search.html", books=books)

# Displays a page with reviews based off the book's isbn number, which is taken as an argument
@app.route("/books/<isbn>")
def book(isbn):
    # Query for book information
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # Query for reviews
    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn ORDER BY id DESC", {"isbn": isbn}).fetchall()

    # Query Goodreads for ratings and review counts
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("GOODREADS_API_KEY"), "isbns": isbn})
    message = None
    gr_book = None
    if res.status_code == 404:
        message = "Goodreads does not have any information for this book"
    else:
        gr_book = res.json()['books'][0]
    
    # If the book is not in the database or in the goodreads database, show an error page instead.
    if not book and not gr_book:
        return render_template("error.html", message="ISBN not in database or in Goodreads database.")

    # Check if the user is logged in
    if 'user' in session:
        #If they are logged in, see if they have a review
        users_review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": session['user']}).fetchone()
        # If they do have a review, show that review in a seperate section
        if users_review:
            return render_template("isbn.html", isbn=isbn, book=book, reviews=reviews, users_review=users_review, gr_book=gr_book, message=message)

    return render_template("isbn.html", isbn=isbn, book=book, reviews=reviews, gr_book=gr_book, message=message)

# User profile pages that display reviews, and also handle posting new reviews from the isbn form.
@app.route("/profile/<user>", methods=["GET", "POST"])
def profile(user):
    # Keep track of if there has been a new review posted
    new_review = False
    if request.method == "POST":
        # Get the users's username
        username = session['user']
        # Get the review variables from the isbn form
        isbn = request.form.get("isbn")
        review = request.form.get("review")
        rating = int(request.form.get("rating"))
        
        # Add the new review to the database
        db.execute("INSERT INTO reviews (isbn, username, review, rating) values (:isbn, :username, :review, :rating)",
                    {"isbn": isbn, "username": username, "review": review, "rating": rating})
        db.commit()
        
        # A new review has been added
        new_review = True
    
    # Get all the user's reviews and store the result
    users_reviews = db.execute("SELECT r.review, r.rating, r.isbn, books.title FROM reviews r LEFT JOIN books ON books.isbn = r.isbn WHERE r.username = :username", 
                                {"username": user})
    return render_template("user.html", user=user, users_reviews=users_reviews, new_review=new_review, message="New review successfully added!")

# A form to add individual books to the database
@app.route("/books/add", methods=["GET","POST"])
def book_add():
    if request.method == "POST":
        # Get the values from the form
        isbn = request.form.get("ISBN")
        title = request.form.get("title")
        author = request.form.get("author")
        try:
            year = int(request.form.get("year"))
        except ValueError:
            return render_template("books-add.html", failed=True, message='The year you entered was not an integer.')
        
        if isbn and title and author and year:
            # If they all have values, add the book to the database
            db.execute("INSERT INTO books (title, author, year, isbn) VALUES (:title, :author, :year, :isbn)", 
                    {"title": title, "author": author, "year": year, "isbn": isbn})
            db.commit()
            return render_template("books-add.html", message="Your book has been added to the database.", success=True)
        else:
            # If any are none, let the user know they need to fill in all the blanks
            return render_template("books-add.html", message="Please fill in all of the boxes!", failed=True)
    else:
        return render_template("books-add.html")

@app.route("/api/<isbn>")
def book_api(isbn):
    # Query for book information in a specific order
    book = db.execute("SELECT title, author, year, isbn FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    print(book)

    # If the book is not in the database, return 404 error
    if not book:
        return jsonify({"error": "ISBN not in database"}), 404

    # Query for review count and average rating
    reviews = db.execute("SELECT COUNT(review) AS review_count, AVG(rating) AS average_score FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    print(reviews)

    # Create the dictionary that will be dumped into a json
    return jsonify({"title": book[0], "author": book[1], "year": book[2], "isbn": book[3], "review_count": reviews[0], "average_score": reviews[1]}), 200
import os

from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

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
        username = request.form.get("username")
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
        username = request.form.get("username")
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
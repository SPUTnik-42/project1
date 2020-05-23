import os, requests, json
from flask import Flask, session, render_template, redirect, url_for, flash, request
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#database_url
DATABASE_URL = "postgres://mpbwycyylmpxxx:ac28ae434f8eb7b635529c2f3dd41042b1bbdcec8c820334f56271e97024eb47@ec2-52-71-55-81.compute-1.amazonaws.com:5432/d1n2s5r3apv588"

#api_key 
GOODREADS_API_KEY = "ya8uM2HkMVhG6V4t7bXjA"

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "Thisissupposedtobesecret"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy()

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

engine = create_engine(os.getenv("DATABASE_URL"))
Dbase = scoped_session(sessionmaker(bind=engine))

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#class for table users
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key =True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)

#class for table books
class Books(db.Model):

    __searchable__ = ['title','author','isbn','year']

    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    author = db.Column(db.String, unique=True)
    year = db.Column(db.String, unique=True)



#class for forms
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=5, max=80)])
    
   
#class for signup
class SignupForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=5, max=80)])



@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login", methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("dashboard"))               
        flash('INVALID USERNAME OR PASSWORD', 'danger')
    return render_template('login.html', form=form)

@app.route("/signup", methods=['GET','POST'])
def signup():
    form = SignupForm()

    email = form.email.data
    username = form.username.data
    

    if form.validate_on_submit():
        #return '<h1>' + form.username.data + ' ' + form.password.data + ' ' + form.email.data  + '</h1>'
        hashed_password = generate_password_hash(form.password.data, method="sha256")
        new_user = Users(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for("login"))
    
    return render_template('signup.html', form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    
    return render_template('dashboard.html', name=current_user.username) #so that the username can be applied to the dashboard
    

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out!", "info")
    return redirect(url_for("index"))

@app.route("/search")
@login_required
def search():
    """ Get books results """

    # Check book id was provided
    if not request.args.get("book"):
        flash("you must provide a book, or select one from below", 'danger')

    # Take input and add a wildcard
    query = "%" + request.args.get("book") + "%"

    # Capitalize all words of input for search
    # https://docs.python.org/3.7/library/stdtypes.html?highlight=title#str.title
    rows = Dbase.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query ",
                        {"query": query})
    
    # Books not founded
    if rows.rowcount == 0:
        flash("we can't find books with that description.", "danger")
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)

@app.route("/book/<isbn>", methods=['POST', 'GET'])
@login_required
def book(isbn):
    #key: ya8uM2HkMVhG6V4t7bXjA
    
    row = Dbase.execute("SELECT isbn, title, author, year FROM books WHERE \
                isbn = :isbn",
                {"isbn": isbn})

    bookInfo = row.fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": isbn})
    avg_rating_Goodreads = res.json()['books'][0]['average_rating']
    number_rating_Goodreads = res.json()['books'][0]['work_ratings_count']
    reviews = Dbase.execute("SELECT comment,rating,user_id FROM reviews WHERE isbn = :isbn", {"isbn": isbn})

    if request.method == "POST":

        # Save current user info
        currentUser = current_user.username
        
        # Fetch form data
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        
        
       

        # Check for user submission (ONLY 1 review/user allowed per book)
        row2 = Dbase.execute("SELECT * FROM reviews WHERE user_id = :user_id AND isbn = :isbn",
                    {"user_id": currentUser,
                     "isbn": isbn})

        # A review already exists
        if row2.rowcount == 1:
            
            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)
         # Convert to save into DB
        rating = int(rating)

        Dbase.execute("INSERT INTO reviews (user_id, isbn, comment, rating) VALUES \
                    (:user_id, :isbn, :comment, :rating)",
                    {"user_id": currentUser, 
                    "isbn": isbn, 
                    "comment": comment, 
                    "rating": rating})

        # Commit transactions to DB and close the connection
        Dbase.commit()

        flash('Review submitted!', 'info')

        return redirect("/book/" + isbn)

    

    
    return render_template("book.html", name=current_user.username,bookInfo = bookInfo, avg_rating_Goodreads = avg_rating_Goodreads,number_rating_Goodreads = number_rating_Goodreads,reviews = reviews)

@app.route("/api/<isbn>")
@login_required
def api(isbn):
    result = Dbase.execute("SELECT title, author, year FROM books WHERE isbn = :isbn",
    {"isbn": isbn})

    # Store result of SELECT-query in a dict
    book_data = dict(result.first())
    book_data['isbn'] = isbn

    # Query Goodreads API for data on book ratings
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": isbn})
    avg_rating_Goodreads = res.json()['books'][0]['average_rating']
    number_rating_Goodreads = res.json()['books'][0]['work_ratings_count']

    # Store data from Goodreads in book_data
    book_data['average_score'] = avg_rating_Goodreads
    book_data['review_count'] = number_rating_Goodreads

    

    # Convert book_data dict into JSON string
    book_json = json.dumps(book_data)

    return book_json

if __name__=="__main__":
    app.run(debug=True)
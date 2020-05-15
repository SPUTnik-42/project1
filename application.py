import os

from flask import Flask, session, render_template, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "Thisissupposedtobesecret"
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

#class for forms
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=5, max=80)])
    remember = BooleanField('remember me')

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
        username = form.username.data
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).fetchall()
        
        if user is not None:
            if user[1] == form.password.data :
                redirect(url_for('dashboard'))
        
        return '<h1>INVALID USERNAME OR PASSWORD</h1>'
    return render_template('login.html', form=form)

@app.route("/signup", methods=['GET','POST'])
def signup():
    form = SignupForm()

    email = form.email.data
    username = form.username.data
    password = form.password.data

    if form.validate_on_submit():
        #return '<h1>' + form.username.data + ' ' + form.password.data + ' ' + form.email.data  + '</h1>'
        db.execute("INSERT INTO users (email, username, password) VALUES(:email, :username, :password)", 
                    {"email":email,"username":username, "password":password}
                )
    db.commit()
    
    return render_template('signup.html', form=form)


@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/foo")
def foo():
    data = db.execute("SELECT * FROM users")
    



if __name__=="__main__":
    app.run(debug=True)
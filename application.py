import os
from model import *
from flask import Flask, session, render_template, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "Thisissupposedtobesecret"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


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


if __name__=="__main__":
    app.run(debug=True)
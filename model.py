from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import flask_whooshalchemy as wa

db = SQLAlchemy()

#class for table users
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key =True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)

class Books(db.Model):

    __searchable__ = ['title','author']

    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    author = db.Column(db.String, unique=True)
    year = db.Column(db.String, unique=True)

wa.whoosh_index(app, Post)




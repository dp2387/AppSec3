import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spell_check.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'

    username = db.Column(db.String(32), primary_key=True)
    password = db.Column(db.String(256), nullable=False)
    mfa = db.Column(db.Integer, nullable=False)

class Spellcheck(db.Model):
    __tablename__ = 'spellcheck'

    username = db.Column(db.String(32),db.ForeignKey(User.username), primary_key=True)
    original_txt = db.Column(db.String(1000), primary_key=True)
    checked_txt = db.Column(db.String(1000), primary_key=True)

    user = db.relationship(User)

class Log(db.Model):
    __tablename__ = 'log'

    query_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(32),db.ForeignKey(User.username))
    query_type = db.Column(db.String(32))
    query_str = db.Column(db.String(1000))
    time = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship(User)

if __name__ == "__main__":
    db.create_all()

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

    query_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(32),db.ForeignKey(User.username))
    time = db.Column(db.DateTime, default=db.func.now())
    query_txt = db.Column(db.String(1000))
    query_result = db.Column(db.String(1000))

    user = db.relationship(User)


class Loginlog(db.Model):
    __tablename__ = 'loginlog'

    query_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(32),db.ForeignKey(User.username))
    time = db.Column(db.DateTime, default=db.func.now())
    query_type = db.Column(db.String(16))

    user = db.relationship(User)

if __name__ == "__main__":
    db.create_all()

import hashlib
import os
import subprocess
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from functools import wraps
from create_db import User, Spellcheck, Log

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spell_check.db'
app.secret_key = "SPELL_CHECK_SECRET"
SALT = "cs9163"
db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("spell_check"))
    return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.form:
        username = request.form["username"]
        plainpwd = request.form["password"] + SALT
        hashedpwd = hashlib.sha256(plainpwd.encode("utf-8")).hexdigest()
        mfa = int(request.form["mfa"])
        user = db.session.query(User).filter_by(username=username).first()

        if not user:
            result = "Incorrect username."
        elif user.password != hashedpwd:
            result = "Incorrect password."
        elif user.mfa != mfa:
            result = "Two-factor authentication failure."
        elif user.password == hashedpwd and user.mfa == mfa:
            session["username"] = username
            result = "login success."
            return render_template("spell_check.html")

        return render_template("login.html", result=result)

    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.form:
        username = request.form["username"]
        plainpwd = request.form["password"] + SALT
        hashedpwd = hashlib.sha256(plainpwd.encode("utf-8")).hexdigest()
        mfa = int(request.form["mfa"])
        try:
            user = User(username=username, password=hashedpwd, mfa=mfa)
            db.session.add(user)
            db.session.commit()
            result = "Registration success."
        except exc.IntegrityError:
            result = "Registration failure. Username is already taken."
        return render_template('register.html', result=result)    
    return render_template('register.html')

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")

@app.route("/spell_check", methods=["POST", "GET"])
@login_required
def spell_check():
    if request.form:
        original_txt = request.form["unchecked"]

        f = open('textout.txt', 'w+')
        f.write(original_txt)
        f.close()

        out = subprocess.Popen(['./spell_check', 'textout.txt', 'wordlist.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(out)
        stdout, stderr = out.communicate()
        checked_txt = stdout.decode().strip()
        misspelled = checked_txt.split()
        os.remove('textout.txt')

        try:
            spellcheck = Spellcheck(username=session["username"], original_txt=original_txt, checked_txt=checked_txt)
            db.session.add(spellcheck)
            db.session.commit()
        except exc.IntegrityError:
            pass

        return render_template('spell_check.html', message=checked_txt)
    return render_template('spell_check.html')

if __name__ == "__main__":
    app.run()

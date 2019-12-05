import hashlib
import os
import subprocess
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from functools import wraps
from create_db import User, Spellcheck, Loginlog
from sqlalchemy.dialects import postgresql

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
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/home", methods=["GET"])
@login_required
def home():
    username = session["username"]
    return render_template("home.html", user=username)

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
            log = Loginlog(username=username, query_type="login")
            db.session.add(log)
            db.session.commit()
            session["username"] = username
            result = "login success."
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
            log = Loginlog(username=username, query_type="register")
            db.session.add(user)
            db.session.add(log)
            db.session.commit()
            result = "Registration success."
        except exc.IntegrityError:
            result = "Registration failure. Username is already taken."
        return render_template('register.html', result=result)    
    return render_template('register.html')

@app.route("/logout", methods=["GET"])
def logout():
    log = Loginlog(username=session["username"], query_type="logout")
    db.session.add(log)
    db.session.commit()
    session.pop("username")
    return redirect("/")

@app.route("/spell_check", methods=["POST", "GET"])
@login_required
def spell_check():
    if request.form:
        original_txt = request.form["unchecked"]
        misspelled = ''

        f = open('textout.txt', 'w+')
        f.write(original_txt)
        f.close()

        out = subprocess.Popen(['./spell_check', 'textout.txt', 'wordlist.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = out.communicate()
        checked_txt = stdout.decode().strip().split()
        for word in checked_txt:
            misspelled += word + ', '
        misspelled = misspelled[:-2]
        os.remove('textout.txt')

        try:
            spellcheck = Spellcheck(username=session["username"], query_txt=original_txt, query_result=misspelled)
            db.session.add(spellcheck)
            db.session.commit()
        except exc.IntegrityError:
            pass

        return render_template('spell_check.html', misspelled=misspelled, original=original_txt)
    return render_template('spell_check.html')


@app.route("/history/query<querynum>", methods=["POST", "GET"])
@login_required
def query(querynum):
    query = db.session.query(Spellcheck).filter_by(query_id=querynum).first()
    return render_template("query.html", query=query, user=session["username"])

@app.route("/history", methods=["POST", "GET"])
@login_required
def history():
    if session["username"] == "admin":
        if request.form:
            query_ct = db.session.query(Spellcheck).filter_by(username=request.form["username"]).count()
            queries = db.session.query(Spellcheck).filter_by(username=request.form["username"]).all()
            return render_template("history.html", queries=queries, count=query_ct, user=session["username"])
        return render_template("history.html", user=session["username"])
    else:
        query_ct = db.session.query(Spellcheck).filter_by(username=session["username"]).count()
        queries = db.session.query(Spellcheck).filter_by(username=session["username"]).all()
        return render_template("history.html", queries=queries, count=query_ct, user=session["username"])
    #return render_template("history.html")

@app.route("/login_history", methods=["POST", "GET"])
@login_required
def login_history():
    username = session["username"]
    if username == "admin":
        if request.form:
            logs = db.session.query(Loginlog).filter_by(username=request.form["uname"]).all()

            return render_template("login_history.html", log=logs, user=username)
        
    return render_template("login_history.html", user=username)

if __name__ == "__main__":
    app.run()


from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import secrets
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DB = "love_app.db"

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def setup():
    db = connect()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS couples (
        code TEXT PRIMARY KEY,
        partner1 TEXT,
        partner2 TEXT
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        sender TEXT,
        message TEXT,
        kind TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.commit()
    db.close()

setup()

STYLE = """
<style>
*{box-sizing:border-box}
body{
 margin:0;padding:20px 12px;
 background:linear-gradient(135deg,#30001d,#92004e,#ff528d);
 font-family:Arial,sans-serif;color:white;text-align:center;
 min-height:100vh;
}
.card{
 max-width:520px;margin:25px auto;padding:25px 18px;
 background:rgba(255,255,255,.13);
 border:1px solid #ffffff55;border-radius:25px;
 box-shadow:0 10px 35px #260014;
}
h1{color:#ffb4d0;font-size:30px}
input{
 width:95%;padding:14px;margin:9px 0;
 border:0;border-radius:12px;font-size:16px;
}
button{
 padding:13px 20px;margin:7px;border:0;
 border-radius:25px;background:#ff287b;
 color:white;font-weight:bold;font-size:15px;
 cursor:pointer;
}
button:hover{background:#d80058}
a{color:#ffd5e5}
.msg{
 background:#ffffff20;border-radius:15px;
 padding:13px;margin:12px 0;text-align:left;
 overflow-wrap:anywhere;
}
small{color:#ffd5e5}
textarea{
 width:96%;height:90px;padding:13px;
 border-radius:12px;border:0;font-size:16px;
}
</style>
"""

HOME = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forever Love ❤️</title>""" + STYLE + """</head>
<body>
<div class="card">
<h1>❤️ FOREVER LOVE ❤️</h1>
<h3>Two Hearts, One Love 💑</h3>
<h2>Create Your Couple Room</h2>
<form action="/create" method="post">
<input name="name" placeholder="Your Name ❤️" required maxlength="30">
<button>Create Couple Room 💕</button>
</form>
<hr>
<h2>Join Your Partner 💌</h2>
<form action="/join" method="post">
<input name="name" placeholder="Your Name" required maxlength="30">
<input name="code" placeholder="Enter Couple Code" required maxlength="12">
<button>Join Love Room ❤️</button>
</form>
<p>Made With Love 🌹 2026</p>
</div></body></html>
"""

ROOM = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Our Love Room ❤️</title>""" + STYLE + """</head>
<body>
<div class="card">
<h1>❤️ Our Love Room ❤️</h1>
<h3>Welcome {{name}} 🥰</h3>
<h3>Couple Code: <span style="color:#ffe09a">{{code}}</span></h3>
<p>Share this code with your partner 💌</p>
<h3>Partner: {{partner}}</h3>
<hr>
<h2>Send Love Message 💕</h2>
<form action="/send" method="post">
<textarea name="message" placeholder="Write something lovely..." required maxlength="1000"></textarea>
<br>
<button name="kind" value="Love">❤️ Send Love</button>
<button name="kind" value="Sorry">🥺 Say Sorry</button>
</form>

<h2>Our Messages 💌</h2>
{% for m in messages %}
<div class="msg">
<b>{{m.sender}}</b>
<small> — {{m.kind}} | {{m.created}}</small>
<p>{{m.message}}</p>
</div>
{% else %}
<p>No messages yet. Send your first love message! ❤️</p>
{% endfor %}

<hr>
<h3>Do you forgive me? 🥺</h3>
<form action="/send" method="post">
<input type="hidden" name="kind" value="Forgive">
<input type="hidden" name="message" value="I forgive you! ❤️">
<button>❤️ I Forgive You</button>
</form>
<form action="/send" method="post">
<input type="hidden" name="kind" value="Love">
<input type="hidden" name="message" value="I Love You Forever! 💖">
<button>💖 I Love You</button>
</form>
<form action="/logout" method="post">
<button style="background:#555">Logout</button>
</form>
<p>Forever Together ❤️</p>
</div></body></html>
"""

@app.route("/")
def home():
    if "code" in session:
        return redirect("/room")
    return render_template_string(HOME)

@app.route("/create", methods=["POST"])
def create():
    name = request.form.get("name", "").strip()
    if not name:
        return "Please enter your name", 400

    code = secrets.token_hex(3).upper()

    db = connect()
    db.execute(
        "INSERT INTO couples(code,partner1,partner2) VALUES(?,?,?)",
        (code, name, "")
    )
    db.commit()
    db.close()

    session["code"] = code
    session["name"] = name
    return redirect("/room")

@app.route("/join", methods=["POST"])
def join():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    db = connect()
    couple = db.execute(
        "SELECT * FROM couples WHERE code=?", (code,)
    ).fetchone()

    if not couple:
        db.close()
        return "Invalid Couple Code! Please try again."

    if couple["partner2"]:
        db.close()
        return "This Couple Room already has two partners."

    if name.lower() == couple["partner1"].lower():
        db.close()
        return "Please enter a different partner name."

    db.execute(
        "UPDATE couples SET partner2=? WHERE code=?",
        (name, code)
    )
    db.commit()
    db.close()

    session["code"] = code
    session["name"] = name
    return redirect("/room")

@app.route("/room")
def room():
    if "code" not in session:
        return redirect("/")

    db = connect()
    couple = db.execute(
        "SELECT * FROM couples WHERE code=?",
        (session["code"],)
    ).fetchone()

    if not couple:
        session.clear()
        db.close()
        return redirect("/")

    messages = db.execute(
        "SELECT * FROM messages WHERE code=? ORDER BY id DESC LIMIT 100",
        (session["code"],)
    ).fetchall()

    partner = (
        couple["partner2"]
        if session["name"] == couple["partner1"]
        else couple["partner1"]
    )

    db.close()

    return render_template_string(
        ROOM,
        name=session["name"],
        partner=partner or "Waiting to join...",
        code=session["code"],
        messages=messages
    )

@app.route("/send", methods=["POST"])
def send():
    if "code" not in session:
        return redirect("/")

    message = request.form.get("message", "").strip()
    kind = request.form.get("kind", "Love")

    if kind not in ("Love", "Sorry", "Forgive"):
        kind = "Love"

    if message:
        db = connect()
        db.execute(
            """INSERT INTO messages(code,sender,message,kind)
               VALUES(?,?,?,?)""",
            (session["code"], session["name"], message, kind)
        )
        db.commit()
        db.close()

    return redirect("/room")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

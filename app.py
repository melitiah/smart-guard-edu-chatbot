from dotenv import load_dotenv
load_dotenv()
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import openai

# -----------------------
# Flask app config
# -----------------------
app = Flask(__name__)
app.secret_key = "your_secret_key"

openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------
# Flask-Login setup
# -----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -----------------------
# User model and storage
# -----------------------
users = {}  # In-memory user store

class User(UserMixin):
    def __init__(self, school_id):
        self.id = school_id

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# -----------------------
# Routes
# -----------------------
@app.route("/")
@login_required
def home():
    return render_template("index.html", user=current_user)

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    user_message = request.json.get("message")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful school assistant chatbot."},
            {"role": "user", "content": user_message}
        ]
    )
    bot_reply = response.choices[0].message.content
    return jsonify({"reply": bot_reply})

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    name = request.form["name"]
    school_id = request.form["school_id"]
    password = request.form["password"]
    school = request.form["school"]

    if school_id in users:
        return "School ID already registered."
    
    users[school_id] = {
        "name": name,
        "password": generate_password_hash(password),
        "school": school
    }

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    school_id = request.form["school_id"]
    password = request.form["password"]
    user_data = users.get(school_id)

    if user_data and check_password_hash(user_data["password"], password):
        user = User(school_id)
        login_user(user)
        return redirect(url_for("home"))
    
    return "Invalid credentials."

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------
# Run app
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)

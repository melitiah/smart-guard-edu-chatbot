from dotenv import load_dotenv
load_dotenv()

from chatbot import get_bot_response

import os
import random
import base64
import io

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import openai
import pyotp
import qrcode

# -----------------------
# App Configuration
# -----------------------

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# 🌍 Supported languages
LANGUAGES = ['en', 'es', 'fr', 'de', 'ht', 'zh']

@app.route('/set-language')
def set_language():
    selected_language = request.args.get('language')
    if selected_language in LANGUAGES:
        session['language'] = selected_language
    return redirect(request.referrer or url_for('login'))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "your_secret_key"

db = SQLAlchemy(app)
openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------
# Mail Configuration
# -----------------------
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
mail = Mail(app)

# -----------------------
# Login Manager
# -----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -----------------------
# User Model
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(200))
    school = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    totp_secret = db.Column(db.String(32))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# -----------------------
# Static Resource Map
# -----------------------
resource_map = {
    "capital of France": [
        {"title": "Geography of France", "url": "https://www.youtube.com/watch?v=example1"},
        {"title": "France Capital - Britannica", "url": "https://www.britannica.com/place/Paris"}
    ],
    "basic arithmetic": [
        {"title": "Addition Basics - Khan Academy", "url": "https://www.khanacademy.org/math/arithmetic"},
        {"title": "2 + 2 Explained", "url": "https://www.youtube.com/watch?v=example2"}
    ]
}


# -----------------------
# Routes
# -----------------------

@app.route("/")
@login_required
def home():
    return render_template("index.html", user=current_user)


@app.route("/chat-with-language", methods=["POST"])
def chat_with_language():
    data = request.get_json()
    user_message = data.get("message", "")
    language = data.get("language", "en")

    print("💬 User Message:", user_message)
    print("🌐 Selected Language:", language)

    try:
        system_prompt = f"""
        You are SmartGuard, a helpful educational assistant for kids.
        Answer clearly and include 1–2 helpful, kid-friendly links for further learning when appropriate.
        Always reply in the user's selected language: {language}.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]
        )

        print("✅ GPT Response:", response)
        reply = response['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ OpenAI error:", str(e))
        return jsonify({"reply": "⚠️ Sorry, something went wrong processing your question."}), 500

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    user_message = request.json.get("message")
    reply = get_bot_response(user_message)  # ✅ from chatbot.py
    return jsonify({"reply": reply})

@app.route("/check-answer", methods=["POST"])
@login_required
def check_answer():
    data = request.json
    user_answer = data.get("user_answer")
    correct_answer = data.get("correct_answer")
    question = data.get("question")
    topic = data.get("topic")

    if user_answer.strip().lower() == correct_answer.strip().lower():
        return jsonify({"result": "correct", "explanation": "✅ That's correct! Good job."})

    prompt = f"""
    The student answered: '{user_answer}' to the question: '{question}'.
    The correct answer is '{correct_answer}'.

    Explain why the student's answer is incorrect and provide a detailed explanation of the correct answer.
    Then, recommend one or two helpful online resources (such as YouTube videos or articles) for further learning.
    Provide clickable links.
    """

    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful tutor that explains answers and recommends learning resources."},
            {"role": "user", "content": prompt}
        ]
    )

    explanation = gpt_response.choices[0].message.content

    extra_resources = resource_map.get(topic, [])
    if extra_resources:
        explanation += "\n\n📚 Additional Resources:"
        for res in extra_resources:
            explanation += f"\n- [{res['title']}]({res['url']})"

    return jsonify({"result": "incorrect", "explanation": explanation})


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"]
    school_id = request.form["school_id"]
    password = request.form["password"]
    school = request.form["school"]
    email = request.form["email"]

    existing_user = User.query.get(school_id)
    if existing_user:
        flash("School ID already registered.")
        return redirect(url_for("register"))

    totp_secret = pyotp.random_base32()
    new_user = User(
        id=school_id,
        name=name,
        password=generate_password_hash(password),
        school=school,
        email=email,
        totp_secret=totp_secret
    )
    db.session.add(new_user)
    db.session.commit()

    otp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(name=email, issuer_name="SmartGuard Chatbot")
    qr = qrcode.make(otp_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("show_qr.html", qr_code=qr_code_base64)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    school_id = request.form["school_id"]
    password = request.form["password"]
    code = request.form["code"]

    user = User.query.get(school_id)
    if user and check_password_hash(user.password, password):
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid TOTP code.")
    else:
        flash("Invalid credentials.")

    return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

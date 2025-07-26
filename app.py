from dotenv import load_dotenv
load_dotenv()

from chatbot import get_bot_response

import openai
import os
import random
import base64
import io

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify
import pyotp
import qrcode

# -----------------------
# App Configuration
# -----------------------

app = Flask(__name__)

# 🌍 Supported languages
LANGUAGES = ['en', 'es', 'fr', 'de', 'ht', 'zh']

@app.route('/set-language', methods=['GET', 'POST'])
def set_language():
    if request.method == 'POST':
        language = request.form.get('language')
    else:
        language = request.args.get('language')
    session['language'] = language
    return redirect(request.referrer or url_for('index'))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
UPLOAD_FOLDER = os.path.join('static', 'profile_pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_fallback_secret")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
import uuid
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    school = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    totp_secret = db.Column(db.String(32))
    profile_image = db.Column(db.String(100), default='profile_pics/default.png')

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
    current_language = session.get('language', 'en')
    user_name = current_user.name.split()[0] if current_user.is_authenticated else "Guest"
    return render_template("index.html", user=current_user, user_name=user_name, language=current_language)

@app.route("/chat-with-language", methods=["POST"])
def chat_with_language():
    data = request.get_json()
    user_message = data.get("message", "")
    language = data.get("language", "en")

    print("💬 User Message:", user_message)
    print("🌐 Selected Language:", language)

    system_prompt = f"""
    You are SmartGuard, a helpful educational assistant for kids.
    Answer clearly and include 1–2 helpful, kid-friendly links for further learning when appropriate.
    Always reply in the user's selected language: {language}.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ],
            temperature=0.7,
            max_tokens=500
        )

        print("✅ GPT Response:", response)
        reply = response['choices'][0]['message']['content'].strip()
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ OpenAI error:", str(e))
        return jsonify({"reply": "⚠️ Sorry, something went wrong processing your question."}), 500

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
    current_language = session.get('language', 'en')

    if request.method == "POST":
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

        otp_uri = pyotp.TOTP(totp_secret).provisioning_uri(name=email, issuer_name="SmartGuard Chatbot")
        qr = qrcode.make(otp_uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        return render_template("show_qr.html", qr_code=qr_code_base64)

    # Show form if GET
    return render_template("register.html", language=current_language)

@app.route("/login", methods=["GET", "POST"])
def login():
    current_language = session.get('language', 'en')

    if request.method == "POST":
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

    # Show form if GET
    return render_template("login.html", language=current_language)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        mfa_reset = request.form.get("reset_mfa") == "on"

        # Check current password if trying to change password or email
        if (new_password or email != current_user.email) and not check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for("profile"))

        if name:
            current_user.name = name
        if email:
            current_user.email = email
        if new_password:
            current_user.password = generate_password_hash(new_password)

        # MFA Reset
        if mfa_reset:
            new_secret = pyotp.random_base32()
            current_user.totp_secret = new_secret

            otp_uri = pyotp.TOTP(new_secret).provisioning_uri(name=current_user.email, issuer_name="SmartGuard Chatbot")
            qr = qrcode.make(otp_uri)
            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            db.session.commit()
            flash("MFA reset. Scan the new QR code below.")
            return render_template("show_qr.html", qr_code=qr_code_base64)

        db.session.commit()
        flash("Profile updated successfully.")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)

@app.route('/update-picture', methods=['POST'])
@login_required
def update_profile_picture():
    if 'profile_image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('home'))

    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        current_user.profile_image = f'profile_pics/{filename}'
        db.session.commit()
        flash('Profile picture updated!', 'success')
        return redirect(url_for('home'))

    flash('Invalid file type', 'danger')
    return redirect(url_for('home'))
# -----------------------

# Helper function to check allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

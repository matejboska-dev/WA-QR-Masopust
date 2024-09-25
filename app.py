from flask import Flask, request, render_template, redirect, url_for, session, flash
import qrcode
import io
import base64
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Model uživatele
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    qr_expiry = db.Column(db.DateTime, nullable=True)

# Registrace uživatele
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            flash('Uživatelské jméno už existuje!')
            return redirect(url_for('register'))
        
        # Vygenerování QR kódu s odkazem na zadání hesla
        expiry_time = datetime.now() + timedelta(minutes=5)
        new_user = User(username=username, password='', qr_expiry=expiry_time)
        db.session.add(new_user)
        db.session.commit()
        
        # Vytvoření QR kódu (nahradit localhost IP adresou vašeho PC)
        qr_url = f'http://192.168.1.5:5000/set_password/{username}'  # Nahraďte vaší IP
        qr_img = qrcode.make(qr_url)
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('ascii')

        return render_template('show_qr.html', qr_code=img_base64)
    
    return render_template('register.html')

# Stránka pro nastavení hesla přes QR kód
@app.route('/set_password/<username>', methods=['GET', 'POST'])
def set_password(username):
    user = User.query.filter_by(username=username).first()
    if not user or datetime.now() > user.qr_expiry:
        flash('QR kód vypršel nebo uživatel neexistuje.')
        return redirect(url_for('register'))

    if request.method == 'POST':
        password = request.form['password']
        user.password = generate_password_hash(password)
        db.session.commit()
        flash('Heslo bylo úspěšně nastaveno!')
        return redirect(url_for('login'))

    return render_template('set_password.html', username=username)

# Přihlašování uživatele
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Nesprávné uživatelské jméno nebo heslo.')
            return redirect(url_for('login'))

        session['user'] = user.username
        flash('Úspěšně přihlášen!')
        return redirect(url_for('home'))
    
    return render_template('login.html')

# Hlavní stránka
@app.route('/home')
def home():
    if 'user' not in session:
        flash('Nejste přihlášen!')
        return redirect(url_for('login'))
    
    return f"Vítejte {session['user']} v našem fiktivním systému!"

# Odhlášení uživatele
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Úspěšně odhlášen!')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)  # Umožňuje přístup z jiné sítě

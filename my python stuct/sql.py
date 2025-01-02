from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import re

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'zugo_database'
app.config['SECRET_KEY'] = 'your_secret_key'  # For flash messages

mysql = MySQL(app)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        errors = []

        # Username validation
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')

        # Phone number validation
        phone_pattern = re.compile(r'^254\d{9}$')
        if not phone_pattern.match(phone):
            errors.append('Invalid phone number. Must start with 254 and have 12 digits')

        # Password validation
        password_pattern = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$')
        if not password_pattern.match(password):
            errors.append('Password must be at least 6 characters, include letter, number, and special character')

        # Password match validation
        if password != confirm_password:
            errors.append('Passwords do not match')

        # Check if username already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            errors.append('Username already exists')

        # If no errors, proceed with registration
        if not errors:
            try:
                # Hash the password (use a secure method like bcrypt)
                hashed_password = hash_password(password)  # Implement secure password hashing

                # Insert new user
                cur.execute(
                    "INSERT INTO users (username, phone, password) VALUES (%s, %s, %s)", 
                    (username, phone, hashed_password)
                )
                mysql.connection.commit()
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            
            except Exception as e:
                flash(f'Registration failed: {str(e)}', 'error')
        
        else:
            # Display validation errors
            for error in errors:
                flash(error, 'error')

        cur.close()

    return render_template('signup.html')

def hash_password(password):
    """
    Securely hash the password.
    Use a strong hashing method like bcrypt
    """
    import bcrypt
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if user:
            # Verify password
            if verify_password(password, user[3]):  # Assuming password is 4th column
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User not found', 'error')

        cur.close()

    return render_template('login.html')

def verify_password(input_password, stored_hash):
    """
    Verify the input password against stored hash
    """
    import bcrypt
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash)

@app.route('/dashboard')
def dashboard():
    # Add authentication check here
    return render_template('user-dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
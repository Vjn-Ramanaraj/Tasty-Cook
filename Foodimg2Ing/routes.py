from flask import Flask, render_template, request, redirect, url_for, session, flash
from Foodimg2Ing import app
from Foodimg2Ing.output import output
import os
import pymysql
from datetime import timedelta
import pymysql.cursors
import re

# Function to get the database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost', 
        user='root',  
        password='',  
        db='loginDB', 
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Set secret key for session management
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        connection.close()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session.permanent = True  # This will make the session persistent
            msg = 'Logged in successfully!'
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email))
            connection.commit()
            msg = 'You have successfully registered!'
        connection.close()
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)


@app.route('/',methods=['GET'])
def home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')


@app.route('/about', methods=['GET'])
def about():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')


@app.route('/',methods=['POST','GET'])
def predict():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    imagefile=request.files['imagefile']
    image_path=os.path.join(app.root_path,'static\\images',imagefile.filename)
    imagefile.save(image_path)
    img="/images/"+imagefile.filename
    title,ingredients,recipe = output(image_path)
    return render_template('predict.html',title=title,ingredients=ingredients,recipe=recipe,img=img)



@app.route('/<samplefoodname>')
def predictsample(samplefoodname):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    imagefile=os.path.join(app.root_path,'static\\images',str(samplefoodname)+".jpg")
    img="/images/"+str(samplefoodname)+".jpg"
    title,ingredients,recipe = output(imagefile)
    return render_template('predict.html',title=title,ingredients=ingredients,recipe=recipe,img=img)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    msg = ''
    if request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()
        connection.close()

        if account:
            session['reset_email'] = email
            return redirect(url_for('reset_password'))
        else:
            msg = 'Email not found in the database!'
    
    return render_template('forgot_password.html', msg=msg)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    msg = ''
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST' and 'newpassword' in request.form and 'confirmpassword' in request.form:
        new_password = request.form['newpassword']
        confirm_password = request.form['confirmpassword']

        if new_password != confirm_password:
            msg = 'Passwords do not match!'
        else:
            email = session['reset_email']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('UPDATE accounts SET password = %s WHERE email = %s', (new_password, email))
            connection.commit()
            connection.close()
            session.pop('reset_email', None)
            msg = 'Password reset successfully!'
            flash(msg, 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', msg=msg)
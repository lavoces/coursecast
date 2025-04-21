from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'mysecretkey'

UPLOAD_FOLDER = 'data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_users():
  with open('users.json') as f:
    return json.load(f)
  
@app.route('/')
def index():
  return redirect(url_for('login'))

@app.route('/predict')
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('predict.html', active_page='predict')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    import pandas as pd
    import os

    data_folder = 'data'
    uploaded_files = os.listdir(data_folder)

    if not uploaded_files:
        flash('No data uploaded yet.', 'warning')
        return redirect(url_for('home'))

    latest_file = max([os.path.join(data_folder, f) for f in uploaded_files], key=os.path.getctime)
    df = pd.read_csv(latest_file)

    num_rows = df.shape[0]
    num_cols = df.shape[1]
    columns = df.columns.tolist()

    return render_template('dashboard.html', num_rows=num_rows, num_cols=num_cols, columns=columns, table=df.head().to_html(classes='table table-striped', index=False), active_page='dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    users = load_users()
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username] == password:
      session['user'] = username
      return redirect(url_for('home'))
    else:
      flash('Invalid username or password', 'danger')
      return redirect(url_for('login'))
  return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists. Try a different one.', 'danger')
            return redirect(url_for('register'))

        users[username] = password
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/home')
def home():
  if 'user' in session:
    return render_template('home.html', username=session['user'], active_page='home')
  else:
    return redirect(url_for('login'))
  
@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files['file']
    if file.filename.endswith('.csv'):
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('File uploaded successfully!', 'success')
    else:
        flash('Only CSV files are allowed.', 'danger')

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
  session.pop('user', None)
  return redirect(url_for('login'))

if __name__ == '__main__':
  app.run(debug=True)
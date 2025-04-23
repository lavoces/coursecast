from flask import Flask, render_template, request, redirect, url_for, session, flash
from dash_app import create_dashboard
import json
import os
from werkzeug.utils import secure_filename
import pandas as pd
import plotly
import plotly.express as px
import plotly.io as pio

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        import pandas as pd

        df_new = pd.read_csv(filepath)
        master_file = os.path.join(app.config['UPLOAD_FOLDER'], 'master_dataset.csv')

        if os.path.exists(master_file):
            df_master = pd.read_csv(master_file)
            df_combined = pd.concat([df_master, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.to_csv(master_file, index=False)
        flash('File uploaded and added to the dataset successfully!', 'success')
    else:
        flash('Only CSV files are allowed.', 'danger')

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
  session.pop('user', None)
  return redirect(url_for('login'))

if __name__ == '__main__':
  create_dashboard(app)
  app.run(debug=True)
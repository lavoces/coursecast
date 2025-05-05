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
    import pandas as pd
    import plotly.graph_objs as go
    import plotly.io as pio
    from sklearn.linear_model import LinearRegression

    # Load and prepare data
    df = pd.read_csv('data/master_dataset.csv')

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['num_of_enrollees'] = pd.to_numeric(df['num_of_enrollees'], errors='coerce')
    df.dropna(subset=['year', 'num_of_enrollees'], inplace=True)

    # Group by year to get total enrollees
    grouped = df.groupby('year')['num_of_enrollees'].sum().reset_index()

    # Train model for total enrollment prediction
    X = grouped[['year']]
    y = grouped['num_of_enrollees']
    model = LinearRegression()
    model.fit(X, y)

    # Predict next year total enrollees
    latest_year = int(grouped['year'].max())
    next_year = latest_year + 1
    future_years = [latest_year + i for i in range(1, 4)]
    future_df = pd.DataFrame(future_years, columns=['year'])
    predicted_enrollees_list = model.predict(future_df).astype(int)

    # Predict for each course and find top 3
    course_predictions = []
    for code, group in df.groupby('code'):
        course_data = group.groupby('year')['num_of_enrollees'].sum().reset_index()

        if len(course_data) >= 2:
            x_course = course_data[['year']]
            y_course = course_data['num_of_enrollees']

            model = LinearRegression()
            model.fit(x_course, y_course)

            prediction_df = pd.DataFrame([[next_year]], columns=['year'])
            predicted = int(model.predict(prediction_df)[0])

            course_predictions.append({
                'code': code,
                'predicted': predicted
            })

    # Sort and select top 3
    top_courses = sorted(course_predictions, key=lambda x: x['predicted'], reverse=True)[:3]

    # Course name mapping
    course_name_map = {
        'BSAg': 'Bachelor of Science in Agriculture',
        'BAC': 'Bachelor Of Arts In Communication',
        'POLSCI': 'Bachelor Of Arts In Political Science',
        'BSSW': 'Bachelor Of Science In Social Work',
        'BSA': 'Bachelor Of Science In Accountancy',
        'BSAIS': 'Bachelor Of Science In Accounting Information System',
        'Entrep': 'BS in Entrepreneurship',
        'BSBA': 'Bachelor Of Science In Business Administration',
        'BSCS': 'Bachelor Of Science In Computer Science',
        'BSEMC': 'Bachelor Of Science In Entertainment And Multimedia Computing',
        'BSIT': 'Bachelor Of Science In Information Technology',
        'CRIM': 'Bachelor Of Science In Criminology',
        'BEEd': 'Bachelor Of Elementary Education',
        'BSEd': 'Bachelor Of Secondary Education',
        'BSCE': 'Bachelor Of Science In Civil Engineering',
        'BSCpE': 'Bachelor Of Science In Computer Engineering',
        'BSEE': 'Bachelor Of Science In Electrical Engineering',
        'BSHM': 'Bachelor Of Science In Hospitality Management',
        'BSTM': 'Bachelor Of Science In Tourism Management',
        'BSBIO': 'Bachelor Of Science In Biology',
        'BIT': 'Bachelor In Industrial Technology',
        'BSF': 'Bachelor Of Science In Fisheries',
        'BSM': 'Bachelor Of Science In Midwifery',
        'BSN': 'Bachelor Of Science In Nursing'
    }

    for course in top_courses:
        course['name'] = course_name_map.get(course['code'], course['code'])

    # Total enrollment trend chart
    fig = go.Figure()
    # Actual data
    fig.add_trace(go.Scatter(
        x=grouped['year'],
        y=grouped['num_of_enrollees'],
        mode='lines+markers',
        name='Actual'
    ))
    # Predicted future years
    fig.add_trace(go.Scatter(
        x=future_years,
        y=predicted_enrollees_list,
        mode='lines+markers',
        line=dict(color='red'),
        name='Predicted'
    ))

    fig.update_layout(
        title='Enrollment Trend with Prediction',
        xaxis_title='Year',
        yaxis_title='Total Enrollees',
        template='plotly_white'
    )
    chart_html = pio.to_html(fig, full_html=False)

    actual_values = []
    for course in top_courses:
       course_code = course['code']
       course_df = df[(df['code'] == course_code) & (df['year'] == latest_year)]
       total_actual = course_df['num_of_enrollees'].sum()
       actual_values.append(total_actual)

    predicted_values = [course['predicted'] for course in top_courses]
    course_labels = [course['name'] for course in top_courses]

    # Bar chart for top 3 course predictions
    bar_fig = go.Figure(data=[
        go.Bar(
            name=f'Actual {latest_year}',
            x=course_labels,
            y=actual_values,
            marker_color='steelblue'
        ),
        go.Bar(
            name=f'Predicted {next_year}',
            x=course_labels,
            y=predicted_values,
            marker_color='orange'
        )
    ])

    bar_fig.update_layout(
        barmode='group',
        title=f'Top 3 Course Enrollment: Actual {latest_year} vs Predicted {next_year}',
        xaxis_title='Course',
        yaxis_title='Number of Enrollees',
        template='plotly_white'
    )
    bar_fig.update_traces(marker_line_color='black', marker_line_width=1.2)
    bar_chart_html = pio.to_html(bar_fig, full_html=False)

    return render_template(
        'predict.html',
        active_page='predict',
        next_year=next_year,
        future_years=future_years,
        predicted_enrollees=predicted_enrollees_list,
        top_courses=top_courses,
        next_year_prediction=predicted_enrollees_list[0],
        chart_html=chart_html,
        bar_chart_html=bar_chart_html
    )

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
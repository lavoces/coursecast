from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import os

external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
    "/static/dashboard.css"
]

def create_dashboard(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dashboard/',
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True
    )

    def load_data():
        master_file = os.path.join('data', 'master_dataset.csv')
        if os.path.exists(master_file):
            df = pd.read_csv(master_file)
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df['num_of_enrollees'] = pd.to_numeric(df['num_of_enrollees'], errors='coerce')
            df.dropna(subset=['year', 'num_of_enrollees'], inplace=True)
            return df
        return pd.DataFrame()

    df = load_data()
    if df.empty:
        dash_app.layout = html.Div("No data available. Please upload a dataset.", style={'color': 'white', 'padding': '20px'})
        return dash_app

    df_year = df.groupby('year')['num_of_enrollees'].sum().reset_index()
    fig1 = px.line(df_year, x='year', y='num_of_enrollees', title='📈 Total Enrollees Per Year')

    df_course = df.groupby('code')['num_of_enrollees'].sum().nlargest(5).reset_index()
    fig2 = px.bar(df_course, x='code', y='num_of_enrollees', title='🏆 Top 5 Courses by Total Enrollees')

    dash_app.layout = html.Div([
        # Navbar
        html.Nav([
            html.Div([
                html.A([
                    html.Img(src="/static/images/image.png", height="30", className="me-2"),
                    "Coursecast"
                ], className="navbar-brand d-flex align-items-center", href="#"),

                html.Ul([
                    html.Li(html.A("Upload", className="nav-link", href="/home"), className="nav-item"),
                    html.Li(html.A("Dashboard", className="nav-link active", href="/dashboard/", style={'fontSize': '1.1rem'}), className="nav-item"),
                    html.Li(html.A("Prediction", className="nav-link", href="/predict"), className="nav-item"),
                ], className="navbar-nav d-flex flex-row gap-3 me-auto"),

                html.Div([
                    html.Span("Welcome", className="text-white mb-0"),
                    html.A("Logout", className="btn btn-outline-light btn-sm", href="/logout")
                ], className="d-flex align-items-center gap-3")
            ], className="container-fluid d-flex justify-content-between align-items-center")
        ], className="navbar navbar-expand-lg navbar-dark bg-dark px-4 py-3"),

        # Main Content
        html.Div([
            html.H2('📊 Dashboard', className='text-white mb-4'),

            html.Div(dcc.Graph(figure=fig1), className='chart-container'),
            html.Div(dcc.Graph(figure=fig2), className='chart-container'),

            html.Div([
                html.Label('Select Year:', className='text-white'),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': int(year), 'value': int(year)} for year in sorted(df['year'].unique())],
                    value=int(df['year'].max())
                ),
                dcc.Graph(id='pie-chart')
            ], className='chart-container'),

            html.Div([
                html.Label('Select Course:', className='text-white'),
                dcc.Dropdown(
                    id='course-dropdown',
                    options=[{'label': name, 'value': name} for name in sorted(df['coursename'].unique())],
                    value=sorted(df['coursename'].unique())[0]
                ),
                dcc.Graph(id='line-chart-course')
            ], className='chart-container')
        ], className="container mt-5")
    ], style={
        'backgroundImage': 'url("/static/images/bg.jpg")',
        'backgroundSize': 'cover',
        'backgroundRepeat': 'no-repeat',
        'backgroundPosition': 'center',
        'minHeight': '100vh'
    })

    @dash_app.callback(
        Output('pie-chart', 'figure'),
        Input('year-dropdown', 'value')
    )
    def update_bar_chart(selected_year):
        filtered_df = df[df['year'] == selected_year]
        bar_df = filtered_df.groupby('coursename')['num_of_enrollees'].sum().reset_index().sort_values(by='num_of_enrollees')
        return px.bar(
        bar_df,
        x='num_of_enrollees',
        y='coursename',
        orientation='h',
        title=f'📊 Course Distribution in {selected_year}',
        labels={'num_of_enrollees': 'Enrollees', 'coursename': 'Course'},
        template='plotly_white'
    )

    @dash_app.callback(
        Output('line-chart-course', 'figure'),
        Input('course-dropdown', 'value')
    )
    def update_course_trend(course_name):
        filtered_df = df[df['coursename'] == course_name]
        trend_df = filtered_df.groupby('year')['num_of_enrollees'].sum().reset_index()
        return px.line(trend_df, x='year', y='num_of_enrollees',
                       title=f'📈 Enrollment Trend for {course_name}')

    return dash_app

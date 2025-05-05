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

    def serve_layout():
        df = load_data()
        if df.empty:
            return html.Div("No data available. Please upload a dataset.",
                            style={'color': 'white', 'padding': '20px'})

        years = sorted(df['year'].unique())
        courses = sorted(df['coursename'].unique())

        return html.Div([
            # Navbar
            html.Nav([
                html.Div([
                    html.A([
                        html.Img(src="/static/images/image.png", height="30", className="me-2"),
                        "Coursecast"
                    ], className="navbar-brand d-flex align-items-center", href="#"),
                    html.Ul([
                        html.Li(html.A("Upload", href="/home", className="nav-link"), className="nav-item"),
                        html.Li(html.A("Dashboard", href="/dashboard/", className="nav-link active"), className="nav-item"),
                        html.Li(html.A("Prediction", href="/predict", className="nav-link"), className="nav-item"),
                    ], className="navbar-nav d-flex flex-row gap-3 me-auto"),
                    html.Div([
                        html.Span("Welcome", className="text-white mb-0"),
                        html.A("Logout", href="/logout", className="btn btn-outline-light btn-sm")
                    ], className="d-flex align-items-center gap-3")
                ], className="container-fluid d-flex justify-content-between align-items-center")
            ], className="navbar navbar-expand-lg navbar-dark bg-dark px-4 py-3"),

            html.Div([
                html.H2('📊 Dashboard', className='text-white mb-4'),

                # Auto-refresh interval
                dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),

                # Total enrollees chart
                html.Div(dcc.Graph(id='total-enrollees-chart'), className='chart-container'),

                # Top 5 courses chart
                html.Div(dcc.Graph(id='top-courses-chart'), className='chart-container'),

                # Year-filtered bar chart
                html.Div([
                    html.Label('Select Year:', className='text-white'),
                    dcc.Dropdown(
                        id='year-dropdown',
                        options=[{'label': int(y), 'value': y} for y in years],
                        value=years[-1]
                    ),
                    dcc.Graph(id='bar-chart')
                ], className='chart-container'),

                # Course trend line chart
                html.Div([
                    html.Label('Select Course:', className='text-white'),
                    dcc.Dropdown(
                        id='course-dropdown',
                        options=[{'label': name, 'value': name} for name in courses],
                        value=courses[0]
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

    dash_app.layout = serve_layout

    @dash_app.callback(
        Output('total-enrollees-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_total_enrollees(_):
        df = load_data()
        df_year = df.groupby('year')['num_of_enrollees'].sum().reset_index()
        fig = px.line(
            df_year, x='year', y='num_of_enrollees',
            title='📈 Total Enrollees Per Year',
            labels={'year': 'Academic Year', 'num_of_enrollees': 'Number of Enrollees'}
        )
        fig.update_traces(line=dict(width=4, color='green'))
        fig.update_layout(template='plotly_white')
        return fig

    @dash_app.callback(
        Output('top-courses-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_top_courses(_):
        df = load_data()
        df_course = df.groupby('code')['num_of_enrollees'].sum().nlargest(5).reset_index()
        fig = px.bar(
            df_course, x='code', y='num_of_enrollees',
            title='🏆 Top 5 Courses by Total Enrollees',
            labels={'code': 'Course', 'num_of_enrollees': 'Number of Enrollees'}
        )
        fig.update_traces(marker_color='skyblue', marker_line_color='black', marker_line_width=1.2)
        fig.update_layout(template='plotly_white', height=500,
                          margin=dict(l=40, r=40, t=60, b=100), xaxis_tickangle=-30)
        return fig

    @dash_app.callback(
        Output('bar-chart', 'figure'),
        Input('year-dropdown', 'value')
    )
    def update_bar_chart(selected_year):
        df = load_data()
        filtered = df[df['year'] == selected_year]
        bar_df = filtered.groupby('coursename')['num_of_enrollees'].sum()\
                         .reset_index().sort_values('num_of_enrollees')
        fig = px.bar(
            bar_df, x='num_of_enrollees', y='coursename', orientation='h',
            title=f'📊 Course Distribution in {selected_year}',
            labels={'num_of_enrollees': 'Enrollees', 'coursename': 'Course'}
        )
        fig.update_layout(template='plotly_white', height=600,
                          margin=dict(l=150, r=50, t=50, b=50))
        fig.update_traces(marker_color='steelblue', width=0.8)
        return fig

    @dash_app.callback(
        Output('line-chart-course', 'figure'),
        Input('course-dropdown', 'value')
    )
    def update_course_trend(course_name):
        df = load_data()
        filtered = df[df['coursename'] == course_name]
        trend_df = filtered.groupby('year')['num_of_enrollees'].sum().reset_index()
        fig = px.line(
            trend_df, x='year', y='num_of_enrollees',
            title=f'📈 Enrollment Trend for {course_name}',
            labels={'year': 'Academic Year', 'num_of_enrollees': 'Number of Enrollees'}
        )
        fig.update_traces(line=dict(width=4, color='green'))
        fig.update_layout(template='plotly_white')
        return fig

    return dash_app

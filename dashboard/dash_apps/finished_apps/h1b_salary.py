import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

df = pd.read_csv('C:\\Users\\DuEvans\\Documents\\h1b_data.csv')
df = df.loc[df['base salary'] < 350000]
df['job_title'] = df['job_title'].astype(str)

app = DjangoDash('h1b_salary', external_stylesheets=external_stylesheets)

app.layout = html.Div([

    dcc.Markdown('''

    Job Titles and Salaries of Publicly Available H1B Records.

    Select any combination of companies and jobs to compare H1B jobs certified in 2019:
    '''),

    dcc.Dropdown(
        id='company_selection',
        options=[
            {'label': c, 'value': c}
            for c in sorted(list(df.search_term.unique()))

        ],
        value=['facebook', 'bloomberg', 'apple', ],
        multi=True,
        clearable=False,
    ),

    dcc.Dropdown(
        id='job_selection',
        options=[
            {'label': c, 'value': c}
            for c in sorted(list(df.job_family.unique()))

        ],
        value=['software engineer', ],
        multi=True,
        clearable=False,
    ),

    dcc.Markdown('''
    Total size of available data
    '''),

    # side by side descriptive charts
    html.Div([
        html.Div([
            dcc.Graph(id='company_count_bar'),
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='job_count_bar'),
        ], className="six columns"),
    ], className="row"),

    dcc.Markdown('''
        Exploratory data by job: salary, job types, and locations
    '''),
    # data exploration charts
    dcc.Graph(id='salary_bars'),
    dcc.Graph(id='job_bar'),
    dcc.Graph(id='state_bar'),


], className='container')


@app.callback(
    Output('salary_bars', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     ]
)
def update_salary_bars(companies, jobs):
    dff = df.loc[df['search_term'].isin(companies)]
    job_df = dff.loc[dff['job_family'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['search_term'] == company]
        company = go.Histogram(
            x=company_df['base salary'],
            name=company,
        )
        all_traces.append(company)

    layout = go.Layout(
        title=f"Salary Distribution by Company",
        xaxis={'title': 'Base Salary (USD)'},
        yaxis={'title': 'count', },
        bargap=0.1,
                       )

    figure = {'data': all_traces, 'layout': layout}

    return figure


@app.callback(
    Output('job_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value')]
)
def update_job_bars(companies, jobs):

    dff = df.loc[df['search_term'].isin(companies)]
    job_df = dff.loc[dff['job_family'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['search_term'] == company]

        job_counts = pd.DataFrame(company_df['job_family'].value_counts())
        job_counts['search_term'] = company
        job_counts = job_counts.rename(columns={'job_family': 'count'})
        job_counts['job_family'] = job_counts.index
        job_counts = job_counts.reset_index(drop=True)


        company = go.Bar(
            y=job_counts['count'],
            x=job_counts['job_family'],
            name=company,
            text=job_counts['count'],
            textposition='auto',

        )
        all_traces.append(company)

    layout = go.Layout(
        title=f"Count of Jobs by Company",
        xaxis={'title': 'Job Family'},
        yaxis={'title': 'count'},
        bargap=0.1,
                       )

    figure = {'data': all_traces, 'layout': layout}

    return figure


@app.callback(
    Output('state_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value')]
)
def update_location_bars(companies, jobs):
    dff = df.loc[df['search_term'].isin(companies)]
    job_df = dff.loc[dff['job_family'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['search_term'] == company]
        state_counts = pd.DataFrame(company_df['state'].value_counts())
        state_counts['search_term'] = company
        state_counts = state_counts.rename(columns={'state': 'count'})
        state_counts['state'] = state_counts.index
        state_counts['pct_total'] = state_counts['count'] / state_counts['count'].sum()
        state_counts = state_counts.reset_index(drop=True)

        company = go.Bar(
            y=state_counts['pct_total'],
            x=state_counts['state'],
            name=company,
        )
        all_traces.append(company)

    layout = go.Layout(title=f"All Job Locations by State", xaxis={'title': 'US State'},
                       yaxis={'title': 'Percent of All Jobs per Company', },
                       bargap=0.1,
                       )

    figure = {'data': all_traces, 'layout': layout}

    return figure

@app.callback(
    Output('company_count_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value')]
)
def update_company_count_bar(companies, jobs):
    """"""
    dff = df.loc[df['search_term'].isin(companies)]
    target_df = dff.loc[dff['job_family'].isin(jobs)]

    company_counts = pd.DataFrame(target_df['search_term'].value_counts())
    company_counts['Company'] = company_counts.index
    company_counts = company_counts.reset_index(drop=True)
    company_counts = company_counts.rename(columns={'search_term': 'count'})

    trace = go.Bar(
        y=company_counts['Company'],
        x=company_counts['count'],
        orientation='h',
        text=company_counts['count'],
        textposition='auto',
    )

    layout = go.Layout(
        title=f"Total Results by Company",
        xaxis={'title': 'count of jobs'},
        yaxis={
            'title': '',
            'automargin': True,
        },
    )

    figure = {'data': [trace], 'layout': layout}

    return figure


@app.callback(
    Output('job_count_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value')]
)

def update_job_count_bar(companies, jobs):
    """"""
    dff = df.loc[df['search_term'].isin(companies)]
    target_df = dff.loc[dff['job_family'].isin(jobs)]

    job_counts = pd.DataFrame(target_df['job_family'].value_counts())
    job_counts['Job Family'] = job_counts.index
    job_counts = job_counts.reset_index(drop=True)
    job_counts = job_counts.rename(columns={'job_family': 'count'})

    trace = go.Bar(
        y=job_counts['Job Family'],
        x=job_counts['count'],
        orientation='h',
        text=job_counts['count'],
        textposition='auto',

    )

    layout = go.Layout(
        title=f"Total Results by Job",
        xaxis={'title': 'count of jobs'},
        yaxis={
            'title': '',
            'automargin': True,
        },
    )

    figure = {'data': [trace], 'layout': layout}

    return figure
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
import dash_table

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


# format the starting dataset
def get_dataset():
    """"""
    url = 'https://media.githubusercontent.com/media/Duwevans/h1b-app/master/data/h1b_disclosure_data.csv'

    #df0 = pd.read_csv(url, low_memory=False)
    df0 = pd.read_csv('/Users/duncanevans/downloads/h1b_disclosure_data.csv', low_memory=False)

    df = df0.copy()
    #import os
    #os.chdir('/Users/duncanevans/downloads')
    #df0.to_csv('h1b_disclosure_data.csv', index=False)

    # standardize pay field
    df['base_salary'] = df['WAGE_RATE_OF_PAY_FROM'].str.replace(
        '$', '',
    ).str.replace(',', '').astype(float)

    # convert columns to strings
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].astype(str)

    # remove words that clutter employer names - LLC, INC, etc
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('LLC', '')
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('INC', '')
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('LLP', '')
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('CORPORATION', '')
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('.COM', '')

    # remove punctuations from employer names
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.replace('[^\w\s]', '')
    df['EMPLOYER_NAME'] = df['EMPLOYER_NAME'].str.strip()

    # convert pay field to annual
    df['annualized_conversion'] = df['WAGE_UNIT_OF_PAY'].map(
        {
            'Year': 1,
            'Hour': 2080,
            'Month': 12,
            'Week': 52,
            'Bi-Weekly': 26,
        }
    )

    df['annual_pay'] = df['base_salary'] * df['annualized_conversion']

    # remove outliers on base salary
    df = df.loc[df['annual_pay'] < 400000]

    # isolate to only technology jobs
    # separate SOC CODE into two groups - first two digits are the major group
    df[['soc_major_group', 'soc_minor_group']] = df['SOC_CODE'].str.split(
        pat='-', expand=True
    )

    # SOC_CODE starts with "15-" - these are "Computer and Mathematical Occupations"
    df_tech = df.loc[df['soc_major_group'] == '15']

    return df, df_tech

df_all, df_tech = get_dataset()

df = df_tech.copy()
df['JOB_TITLE'] = df['JOB_TITLE'].astype(str)

# get count of all companies as a list
x = pd.DataFrame(df['EMPLOYER_NAME'].value_counts())
x['EMPLOYER_NAME'] = x.index
sorted_companies = x['EMPLOYER_NAME'].tolist()

# get count of all jobs as a list
x = pd.DataFrame(df['SOC_NAME'].value_counts())
x['SOC_NAME'] = x.index
sorted_jobs = x['SOC_NAME'].tolist()

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
            for c in sorted_companies

        ],
        value=['GOOGLE', 'AMAZON Services', 'MICROSOFT', ],
        multi=True,
        clearable=False,
    ),

    dcc.Dropdown(
        id='job_selection',
        options=[
            {'label': c, 'value': c}
            for c in sorted_jobs

        ],
        value=['SOFTWARE DEVELOPERS, APPLICATIONS', ],
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
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    job_df = dff.loc[dff['SOC_NAME'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['EMPLOYER_NAME'] == company]
        company = go.Histogram(
            x=company_df['annual_pay'],
            name=company,
        )
        all_traces.append(company)

    layout = go.Layout(
        title=f"Salary Distribution by Company",
        xaxis={'title': 'Annual Pay (USD)'},
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

    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    job_df = dff.loc[dff['SOC_NAME'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['EMPLOYER_NAME'] == company]

        job_counts = pd.DataFrame(company_df['SOC_NAME'].value_counts())
        job_counts['EMPLOYER_NAME'] = company
        job_counts = job_counts.rename(columns={'SOC_NAME': 'count'})
        job_counts['SOC_NAME'] = job_counts.index
        job_counts = job_counts.reset_index(drop=True)


        company = go.Bar(
            y=job_counts['count'],
            x=job_counts['SOC_NAME'],
            name=company,
            text=job_counts['count'],
            textposition='auto',

        )
        all_traces.append(company)

    layout = go.Layout(
        title=f"Count of Jobs by Company",
        xaxis={'title': 'SOC NAME'},
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
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    job_df = dff.loc[dff['SOC_NAME'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['EMPLOYER_NAME'] == company]
        state_counts = pd.DataFrame(company_df['EMPLOYER_STATE'].value_counts())
        state_counts['EMPLOYER_NAME'] = company
        state_counts = state_counts.rename(columns={'EMPLOYER_STATE': 'count'})
        state_counts['EMPLOYER_STATE'] = state_counts.index
        state_counts['pct_total'] = round(state_counts['count'] / state_counts['count'].sum(),3)
        state_counts = state_counts.reset_index(drop=True)

        company = go.Bar(
            y=state_counts['pct_total'],
            x=state_counts['EMPLOYER_STATE'],
            name=company,
            text=state_counts['pct_total'],

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
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    target_df = dff.loc[dff['SOC_NAME'].isin(jobs)]

    company_counts = pd.DataFrame(target_df['EMPLOYER_NAME'].value_counts())
    company_counts['Company'] = company_counts.index
    company_counts = company_counts.reset_index(drop=True)
    company_counts = company_counts.rename(columns={'EMPLOYER_NAME': 'count'})

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
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    target_df = dff.loc[dff['SOC_NAME'].isin(jobs)]

    job_counts = pd.DataFrame(target_df['SOC_NAME'].value_counts())
    job_counts = job_counts.rename(columns={'SOC_NAME': 'count'})
    job_counts['SOC_NAME'] = job_counts.index
    job_counts = job_counts.reset_index(drop=True)

    trace = go.Bar(
        y=job_counts['SOC_NAME'],
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
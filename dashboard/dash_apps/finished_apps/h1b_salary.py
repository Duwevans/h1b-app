import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
import dash_table

external_stylesheets = ["https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap-grid.min.css"]


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

# get count of all states as a list
x = pd.DataFrame(df['WORKSITE_STATE'].value_counts())
x['WORKSITE_STATE'] = x.index
sorted_states = x['WORKSITE_STATE'].tolist()

# get counts of all jobs by companies as a table
#job_detail_data = pd.DataFrame(
#    pd.pivot_table(
#        job_df, index=['SOC_NAME'], columns=['EMPLOYER_NAME'],
#        values=['JOB_TITLE'], aggfunc=len
#    ).to_records()
#)
#job_detail_data.columns = job_detail_data.columns.str.replace(
#    "JOB_TITLE", "").str.replace('[^\w\s]', '').str.strip()


app = DjangoDash('h1b_salary', external_stylesheets=external_stylesheets)


app.layout = html.Div([

    dcc.Markdown('''

    # Analysis of Publicly Available H1B Records

    #### Select any combination of companies and jobs to compare H1B jobs certified in 2019:
    '''),

    dcc.Dropdown(
        id='job_selection',
        options=[
            {'label': c, 'value': c}
            for c in sorted_jobs

        ],
        value=['SOFTWARE DEVELOPERS, APPLICATIONS',],
        multi=True,
        clearable=False,
    ),

    dcc.Markdown('''
    
    #### Select companies to compare records:
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
    dcc.Markdown('''
    #### Select states to filter:
    '''),

    dcc.Dropdown(
        id='state_selection',
        options=[
            {'label': c, 'value': c}
            for c in sorted_states

        ],
        value=['CA', 'WA', 'NY', 'NJ', 'TX', ],
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
        ],
            style={'width': '38%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='job_count_bar'),
        ],
            style={'width': '48%', 'display': 'inline-block', 'align': 'right'})
    ],
        ),

    dcc.Markdown('''
        Exploratory data by job: salary, job types, and locations
    '''),
    # data exploration charts
    dcc.Graph(id='salary_bars'),

    # todo: salary descriptive bar chart
    dcc.Graph(id='salary_bar_descriptive'),
    dcc.Graph(id='state_bar'),
    dcc.Graph(id='all_job_count_bars'),
    dcc.Graph(id='all_company_count_bars',
              style={
                  'height': 800,
              }),

], className='container')



@app.callback(
    Output('all_job_count_bars', 'figure'),
    [Input('company_selection', 'value'),
     Input('state_selection', 'value')]
)
def update_all_job_count_bars(companies, states):
    target_df = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    target_df = target_df.loc[target_df['WORKSITE_STATE'].isin(states)]

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
        title=f"Total Results by Company by Job",
        xaxis={'title': 'count of jobs'},
        yaxis={
            'title': '',
            'automargin': True,
            'autorange': 'reversed',
        },
    )

    figure = {'data': [trace], 'layout': layout}

    return figure



@app.callback(
    Output('salary_bars', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     Input('state_selection', 'value'),
     ]
)
def update_salary_bars(companies, jobs, states):
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    states_df = dff.loc[dff['WORKSITE_STATE'].isin(states)]
    job_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

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
    Output('salary_bar_descriptive', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     Input('state_selection', 'value'),
     ]
)
def update_salary_bar_descriptive(companies, jobs, states):
    """calculate 25th, 50th, and 75th percentile annual per each company"""
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    states_df = dff.loc[dff['WORKSITE_STATE'].isin(states)]
    job_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

    all_traces = []
    salaries_pivoted = pd.DataFrame()

    company_pivot = job_df.groupby('EMPLOYER_NAME')['annual_pay'].describe()
    company_pivot['EMPLOYER_NAME'] = company_pivot.index
    display_columns = ['25%', '50%', '75%']
    for i in display_columns:

        trace = go.Bar(
                y=company_pivot[i],
                x=company_pivot['EMPLOYER_NAME'],
                text=company_pivot['50%'],
            )
        all_traces.append(trace)

    layout = go.Layout(
        title=f"Salary Distribution by Company",
        xaxis={'title': 'employer'},
        yaxis={'title': 'annual pay', },
    )

    figure = {'data': [all_traces], 'layout': layout}

    return figure


@app.callback(
    Output('state_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     Input('state_selection', 'value')]
)
def update_location_bars(companies, jobs, states):
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    states_df = dff.loc[dff['WORKSITE_STATE'].isin(states)]
    job_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

    all_traces = []
    for company in companies:
        company_df = job_df.loc[job_df['EMPLOYER_NAME'] == company]
        state_counts = pd.DataFrame(company_df['WORKSITE_STATE'].value_counts())
        state_counts['EMPLOYER_NAME'] = company
        state_counts = state_counts.rename(columns={'WORKSITE_STATE': 'count'})
        state_counts['WORKSITE_STATE'] = state_counts.index
        state_counts['pct_total'] = round(state_counts['count'] / state_counts['count'].sum(), 2)
        # remove <1% in state counts
        state_counts = state_counts.loc[state_counts['pct_total'] >= .01]
        state_counts = state_counts.reset_index(drop=True)

        company = go.Bar(
            y=state_counts['pct_total'],
            x=state_counts['WORKSITE_STATE'],
            name=company,
            text=state_counts['pct_total'],

        )
        all_traces.append(company)

    layout = go.Layout(title=f"All Job Locations by State", xaxis={'title': 'US State'},
                       yaxis={
                           'title': 'Percent of All Jobs per Company',
                           'tickformat': ",.0%",
                           'hoverformat': ",.0%",
                        },
                       bargap=0.1,
                       )

    figure = {'data': all_traces, 'layout': layout}

    return figure

@app.callback(
    Output('company_count_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     Input('state_selection', 'value')]
)
def update_company_count_bar(companies, jobs, states):
    """"""
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    states_df = dff.loc[dff['WORKSITE_STATE'].isin(states)]
    target_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

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
            'autorange': 'reversed',
        },
    )

    figure = {'data': [trace], 'layout': layout}

    return figure


@app.callback(
    Output('job_count_bar', 'figure'),
    [Input('company_selection', 'value'),
     Input('job_selection', 'value'),
     Input('state_selection', 'value')]
)

def update_job_count_bar(companies, jobs, states):
    """"""
    dff = df.loc[df['EMPLOYER_NAME'].isin(companies)]
    states_df = dff.loc[dff['WORKSITE_STATE'].isin(states)]
    target_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

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


@app.callback(
    Output('all_company_count_bars', 'figure'),
    [Input('job_selection', 'value'),
     Input('state_selection', 'value')]
)
def update_all_company_count_bars(jobs, states):
    """updates chart that shows all companies with results for
    the target SOC_NAME (job family)"""
    states_df = df.loc[df['WORKSITE_STATE'].isin(states)]
    target_df = states_df.loc[states_df['SOC_NAME'].isin(jobs)]

    company_job_counts = pd.DataFrame(target_df['EMPLOYER_NAME'].value_counts())
    company_job_counts = company_job_counts.rename(columns={'EMPLOYER_NAME': 'count'})
    company_job_counts['EMPLOYER_NAME'] = company_job_counts.index
    company_job_counts = company_job_counts.reset_index(drop=True)

    # only show the first n values
    company_job_counts = company_job_counts.head(25)

    trace = go.Bar(
        y=company_job_counts['EMPLOYER_NAME'],
        x=company_job_counts['count'],
        orientation='h',
        text=company_job_counts['count'],
        textposition='auto',

    )

    layout = go.Layout(
        title=f"Total Results by Job by Company",
        xaxis={'title': 'count of jobs'},
        yaxis={
            'title': '',
            'automargin': True,
            'autorange': 'reversed',
        },
    )

    figure = {'data': [trace], 'layout': layout}

    return figure

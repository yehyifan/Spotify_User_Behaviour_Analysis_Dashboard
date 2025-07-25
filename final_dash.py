# -*- coding: utf-8 -*-
"""Final_Dash.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1gP3RxCHBRAMjKM2e2gLPBIGYzYRYYEpQ

# Install & Import Packages
"""

# pip install dash

# pip install dash-bootstrap-components

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from urllib import request

"""# Load Data"""

# Load dataset
dataset_url = "https://drive.google.com/uc?export=view&id=1Dx65HYqbI4xDlzkCe3ZaZ6gzyzwIvvvb"
name = 'Spotify_data.csv'
with request.urlopen(dataset_url) as f, open(name, 'w') as outf:
    outf.write(f.read().decode('ISO-8859-1'))
df = pd.read_csv(name)
df.head()

"""# Data Preprocessing"""

df.columns.values[0] = 'Age'

# Map ages into consistent groups
def map_age_group(age_val):
    age_val = str(age_val).strip()
    if age_val == '6 to 12':
        return "6-12"
    elif age_val == '12 to 20':
        return "12-20"
    elif age_val == '20 to 35':
        return "20-35"
    elif age_val == '35 to 60':
        return "35-60"
    elif age_val == '60 and above':
        return "60+"
    else:
        return "Unknown"

df['AgeGroup'] = df['Age'].apply(map_age_group)
df['Gender'] = df['Gender'].astype(str).str.strip()
df['spotify_subscription_plan'] = df['spotify_subscription_plan'].astype(str).str.strip()
df['music_recc_rating'] = pd.to_numeric(df['music_recc_rating'], errors='coerce')


"""# Data Visualising"""

# Dash App setup
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H3("Spotify Users in Focus: Plan Selection and Mood-Driven Listening", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Select Age Range:"),
            dcc.Dropdown(
                options=[{"label": a, "value": a} for a in ['All', '6-12', '12-20', '20-35', '35-60', '60+']],
                value='All', id='age-filter'
            ),
            html.Label("Select Gender:"),
            dcc.Dropdown(
                options=[{"label": g, "value": g} for g in ['All', 'Female', 'Male', 'Others']],
                value='All', id='gender-filter'
            ),
            html.Label("Subscription Plan:"),
            dcc.Dropdown(
                options=[{"label": s, "value": s} for s in ['All', 'Free', 'Premium']],
                value='All', id='sub-filter'
            ),
            html.Label("Music Recommendation System Rating:"),
            dcc.Checklist(
                options=[{"label": str(r), "value": r} for r in range(1, 6)],
                value=[1, 2, 3, 4, 5], id='rating-filter', inline=True
            ),
        ], width=3),

        dbc.Col([
            dcc.Graph(id='bar-chart', style={"height": "450px"}),
            dcc.Graph(id='bubble-chart', style={"height": "500px"}),
        ], width=9)
    ])
])

@app.callback(
    [Output('bar-chart', 'figure'), Output('bubble-chart', 'figure')],
    [Input('age-filter', 'value'),
     Input('gender-filter', 'value'),
     Input('sub-filter', 'value'),
     Input('rating-filter', 'value')]
)
def update_charts(age, gender, sub, ratings):
    dff = df.copy()

    if age != "All":
        dff = dff[dff['AgeGroup'] == age]
    if gender != "All":
        dff = dff[dff['Gender'] == gender]
    if sub != "All":
        dff = dff[dff['spotify_subscription_plan'].str.contains(sub, case=False, na=False)]
    if ratings:
        dff = dff[dff['music_recc_rating'].isin(ratings)]

    # Bar chart data
    df_bar = dff[['spotify_usage_period', 'preffered_premium_plan']].dropna()
    usage_order = ["Less than 6 months", "6 months to 1 year", "1 year to 2 years", "More than 2 years"]
    plan_order = ["Student Plan-Rs 59/month", "Individual Plan- Rs 119/ month",
                  "Duo plan- Rs 149/month", "Family Plan-Rs 179/month"]
    df_bar['spotify_usage_period'] = pd.Categorical(df_bar['spotify_usage_period'], usage_order, ordered=True)
    df_bar['preffered_premium_plan'] = pd.Categorical(df_bar['preffered_premium_plan'], plan_order, ordered=True)

    grouped = df_bar.groupby(['spotify_usage_period', 'preffered_premium_plan'], observed=True).size().reset_index(name='User Count')
    total = grouped['User Count'].sum()
    grouped['Percentage'] = (grouped['User Count'] / total * 100).round(2)


    # Bar chart
    spotify_colors = ['#1DB954', '#191414', '#3C3C3C', '#B3B3B3']  # Customized color

    bar_fig = px.bar(
        grouped,
        x='spotify_usage_period',
        y='User Count',
        color='preffered_premium_plan',
        barmode='group',
        color_discrete_sequence=spotify_colors,
        hover_data={'Percentage': True},
        text_auto=True
    )

    bar_fig.update_layout(
        xaxis_title='Usage Period',
        yaxis_title='Number of Users',
        plot_bgcolor='#F9F9F9',
        paper_bgcolor='#F9F9F9',
        height=500,
        title={
            'text': 'Preferred Spotify Premium Plans by User Tenure',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        legend_title_text='Preferred Premium Plan',
        font=dict(color='#3C3C3C')
    )


    # Bubble chart data
    mood_freq = dff[['music_Influencial_mood', 'music_lis_frequency']].dropna()
    mood_freq = mood_freq.assign(
        music_Influencial_mood=mood_freq['music_Influencial_mood'].str.split(',')
    ).explode('music_Influencial_mood')
    mood_freq = mood_freq.assign(
        music_lis_frequency=mood_freq['music_lis_frequency'].str.split(',')
    ).explode('music_lis_frequency')

    mood_freq['music_Influencial_mood'] = mood_freq['music_Influencial_mood'].str.strip().str.title()
    mood_freq['music_lis_frequency'] = mood_freq['music_lis_frequency'].str.strip().str.title()

    mood_freq_counts = mood_freq.groupby(['music_Influencial_mood', 'music_lis_frequency']).size().reset_index(name='Counts')

    # Bubble chart
    bubble_fig = px.scatter(
        mood_freq_counts,
        x='music_lis_frequency',
        y='music_Influencial_mood',
        size='Counts',
        color='Counts',
        color_continuous_scale=['#191414', '#1DB954'],  # Spotify black to green
        size_max=60,
        labels={
            'music_lis_frequency': 'Listening Frequency',
            'music_Influencial_mood': 'Influential Mood',
            'Counts': 'User Count'
        }
    )

    bubble_fig.update_layout(
        xaxis_title="Listening Frequency",
        yaxis_title="Influential Mood",
        height=650,
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={
            'text': 'Influential Moods Across Listening Contexts',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        coloraxis_colorbar=dict(
        title=dict(text='User Count', font=dict(size=14)),
        tickfont=dict(color='#333')
        )
    )


    return bar_fig, bubble_fig

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)

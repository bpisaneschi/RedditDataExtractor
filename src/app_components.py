from dash.dependencies import Input, Output, State
from dash import dcc, html, ctx
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash
import pandas as pd

subreddit_graph_data = pd.read_feather('https://www.googleapis.com/drive/v3/files/1--AaZA3iAwR5wOYVFGhwcP1MbuyN9BUz?alt=media&key=AIzaSyDMT0mK3YGByRkdxToNYGdLfvr_ucGIKrE')
# labeled_data = pd.read_feather('https://www.googleapis.com/drive/v3/files/1IMqhvQ7d33dt_Sw8wg40PX1DZOvDYfif?alt=media&key=AIzaSyDMT0mK3YGByRkdxToNYGdLfvr_ucGIKrE')

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.LUX],
                )


# components

reddit_logo = html.Img(
    src=app.get_asset_url('Reddit-logo.png'),
    id = 'reddit_logo',
    style = {'float':'right'}
)

app_header = html.H1(
    "Crypto Sentiment Dashboard",
    style = {'text-align': 'left','font-weight':'bold','font':'VAG Rounded'}
)

subreddit_select_text = html.P(
    "Select a Subreddit Type or Subreddit",
    style = {'font-weight':'bold'}
)

subtype_text = html.P(
    "Subreddit Type:",
    style = {'padding-top':'5%','font-weight':'bold'}
)

subreddit_text = html.P(
    "Subreddit:",
    style = {'padding-top':'5%','font-weight':'bold'}
)

sub_types = ['crypto','non-crypto']

subreddits = [sub for sub in subreddit_graph_data['sub_type'].unique() if sub not in sub_types]

subtype_checklist_items = dcc.Checklist(
    id = 'subtype_checklist_items',
    labelStyle={'display':'block','padding-left':'5%'},
    options = [{'label':sub_type,'value':sub_type} for sub_type in sub_types],
    value = ['crypto','non-crypto'],
    inputStyle={"margin-right": "10px"}
)

subreddit_checklist_items = dcc.Checklist(
    id = 'subreddit_checklist_items',
    labelStyle={'display':'block','padding-left':'5%'},
    options = [{'label':subreddit,'value':subreddit} for subreddit in subreddits],
    inputStyle={"margin-right": "10px"}
)

metric_select_text = html.P(
    "Select a Daily Sentiment Metric:",
    style = {'font-wight':'bold','text-align':'right'}
)

metric_options = ['Avgerage','3-Day Moving Avg','5-Day Moving Avg','5-Day Exp Moving Avg']

metric_radio_items = dcc.RadioItems(
    id='metric_radio_items', 
    labelStyle = {'display':'inline','padding-left':'5%'},
    options = [{'label':metric,'value':metric} for metric in metric_options],
    value = '5-Day Exp Moving Avg',
    inputStyle={"margin-right": "10px"}
)

isolate_word_input = dcc.Input(
    id='isolate_word_input',
    placeholder='Input a seed word to isolate',
    debounce=True
)

isolate_word_text = html.P(
    "Input seed words to isolate:",
    style = {'font-wight':'bold','text-align':'right'}
)

second_axis_ticker_input = dcc.Input(
    id = 'ticker_input', 
    placeholder= 'Input a ticker to compare',
    value = 'BTC-USD',
    debounce=True,
)

input_ticker_text = html.P(
    "Input a ticker to compare to the sentiment:",
    style = {'font-wight':'bold','text-align':'right'}
)

main_graph = dcc.Graph(
    id = 'main_graph',
)

#blocks

subreddit_select_block = dbc.Col([
    subreddit_select_text,
    subtype_text,
    subtype_checklist_items,
    subreddit_text,
    subreddit_checklist_items,
])

header_block = dbc.Row([
    dbc.Col(reddit_logo,width=4),
    dbc.Col(app_header)
])

metric_block = dbc.Row([
    dbc.Col(metric_select_text,width=3),
    dbc.Col(metric_radio_items)
])

isolate_word_block = dbc.Row([
    dbc.Col(isolate_word_text,width=3),
    dbc.Col(isolate_word_input)
])

second_axis_input_block = dbc.Row([
    dbc.Col(input_ticker_text),
    dbc.Col(second_axis_ticker_input)
])

graph_and_metric_block = dbc.Col([
    metric_block,
    # isolate_word_block,
    main_graph,
    second_axis_input_block
])

main_graph_block = dbc.Row([
    dbc.Col(subreddit_select_block,width=2,align='center'),
    dbc.Col(graph_and_metric_block,width=10),
])
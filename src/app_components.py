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
    "Sentiment Dashboard",
    style = {'text-align': 'left','font-weight':'bold','font':'VAG Rounded'}
)

subreddit_radio_items = dcc.Checklist(
    id = 'subreddit_radio_items',
    labelStyle={'padding-top':'5%','display':'block','padding-left':'5%'},
    options = [{'label':subreddit,'value':subreddit} for subreddit in subreddit_graph_data['sub_type'].unique()],
    value = ['crypto','non-crypto'],
    inputStyle={"margin-right": "10px"}
)

metric_select_text = html.P(
    "Select a Sentiment Metric:",
    style = {'font-wight':'bold','text-align':'right'}
)

metric_options = ['mean','3dayma','5dayma','5dayema']

metric_radio_items = dcc.RadioItems(
    id='metric_radio_items', 
    labelStyle = {'display':'inline','padding-left':'5%'},
    options = [{'label':metric,'value':metric} for metric in metric_options],
    value = '5dayema'
)

isolate_word_input = dcc.Input(
    id='isolate_word_input',
    placeholder='Input a seed word to isolate',
    debounce=True
)

isolate_word_text = html.P(
    "Input a seed word to isolate in the data:",
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
    isolate_word_block,
    main_graph,
    second_axis_input_block
])

main_graph_block = dbc.Row([
    dbc.Col(subreddit_radio_items,width=2,align='center'),
    dbc.Col(graph_and_metric_block,width=10),
])
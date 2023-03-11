import yfinance as yf
from app_components import *

server = app.server

app.layout = html.Div([
    header_block,
    main_graph_block
])

def get_price_history(ticker,start,end):
    close = yf.Ticker(ticker).history(start=start, end=end).loc[:,['Close']].reset_index().rename(columns={'Date':'date','Close':ticker})
    close['3dayma'] = close[ticker].rolling(window=3).mean()
    close['5dayma'] = close[ticker].rolling(window=5).mean()
    close['date'] = pd.DatetimeIndex(close['date'])
    return close

def get_start_end(df):
    df = df.sort_values(by='date')
    dates = list(df['date'])
    start = dates[0]
    end = dates[-1] + pd.Timedelta(days=1)
    return start, end

@app.callback(Output('main_graph','figure'),[Input('subreddit_radio_items','value'),Input('metric_radio_items','value'),Input('ticker_input','value')])
def generate_main_graph(subreddits,metric,compare_ticker):
    metric_dict = {'mean':'Daily Average','5dayma':'5-Day Moving Avg','3dayma':'3-Day Moving Avg','5dayema':'5-Day Exp Moving Avg'}
    start, end = get_start_end(subreddit_graph_data)
    close = get_price_history(compare_ticker,start,end)
    fig = go.Figure()
    for sub in subreddits:
        filter = subreddit_graph_data['sub_type'] == sub
        data = subreddit_graph_data[filter]
        fig.add_trace(go.Scatter(x=data.date,y=data[metric],name=sub))
    fig.add_trace(go.Scatter(x=close['date'],y=close[compare_ticker],name=compare_ticker,yaxis='y2'))
    fig.update_layout(title = {'text':f'Reddit Sentiment vs {compare_ticker} Close Price','x':0.5,'xanchor':'center'},
                xaxis_title='Date',
                yaxis=dict(title=f'{metric_dict[metric]} Sentiment'),
                yaxis2=dict(title=f'{compare_ticker} Close',overlaying='y',side='right'))
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
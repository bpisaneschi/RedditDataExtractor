import yfinance as yf
from app_components import *

server = app.server

app.layout = html.Div([
    header_block,
    main_graph_block
])

def group_and_create_rolling(df,groupby_cols,inclusion_threshold):
    df_grouped = df.groupby(groupby_cols + [df.index]).agg({'labels':['mean','count']})['labels'].reset_index()
    filter = df_grouped['count']>inclusion_threshold
    df_grouped_filtered = df_grouped[filter]
    df_grouped_filtered.loc[:,'3dayma'] = df_grouped_filtered.groupby(groupby_cols)['mean'].transform(lambda x: x.rolling(window=3).mean())
    df_grouped_filtered.loc[:,'5dayma'] = df_grouped_filtered.groupby(groupby_cols)['mean'].transform(lambda x: x.rolling(window=5).mean())
    df_grouped_filtered.loc[:,'5dayema'] = df_grouped_filtered.groupby(groupby_cols)['mean'].transform(lambda x: x.ewm(span=5,axis=0).mean())
    return df_grouped_filtered

def generate_final_graph_datasets(df,isolation_word,probability_threshold=.5,inclusion_threshold=1):
    include_columns = ['date','subreddit','sub_type','body','labels','score']
    filter = (df['score'] >= probability_threshold) & (df['body'].str.contains(isolation_word))
    df.loc[:,'sub_type'] = df['subreddit'].apply(lambda x: determine_crypto(x))
    final_filtered_df = df.loc[filter,include_columns].set_index('date')
    crypto_non_crypto_grouped = group_and_create_rolling(final_filtered_df,['sub_type'],inclusion_threshold)
    subreddit_grouped = group_and_create_rolling(final_filtered_df,['subreddit'],inclusion_threshold)
    combined_grouped = pd.concat([crypto_non_crypto_grouped,subreddit_grouped])
    combined_grouped['sub_type'] = combined_grouped['sub_type'].fillna(combined_grouped['subreddit'])
    return combined_grouped

def determine_crypto(x):
    crypto_subs  = ['CryptoCurrency','bitcoin']
    return 'crypto' if x in crypto_subs else 'non-crypto'

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

@app.callback(Output('main_graph','figure'),[Input('subreddit_radio_items','value'),Input('metric_radio_items','value'),Input('ticker_input','value'),Input('isolate_word_input','value')])
def generate_main_graph(subreddits,metric,compare_ticker,isolation_word):
    data = generate_final_graph_datasets(labeled_data,isolation_word) if isolation_word else subreddit_graph_data
    metric_dict = {'mean':'Daily Average','5dayma':'5-Day Moving Avg','3dayma':'3-Day Moving Avg','5dayema':'5-Day Exp Moving Avg'}
    start, end = get_start_end(subreddit_graph_data)
    close = get_price_history(compare_ticker,start,end)
    fig = go.Figure()
    for sub in subreddits:
        filter = (data['sub_type'] == sub)
        filtered_data = data[filter]
        fig.add_trace(go.Scatter(x=filtered_data.date,y=filtered_data[metric],name=sub))
    fig.add_trace(go.Scatter(x=close['date'],y=close[compare_ticker],name=compare_ticker,yaxis='y2'))
    fig.update_layout(title = {'text':f'Reddit Sentiment vs {compare_ticker} Close Price','x':0.5,'xanchor':'center'},
                xaxis_title='Date',
                yaxis=dict(title=f'{metric_dict[metric]} Sentiment'),
                yaxis2=dict(title=f'{compare_ticker} Close',overlaying='y',side='right'))
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
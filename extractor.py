import pandas as pd
from pmaw import PushshiftAPI 
from datetime import datetime as dt

api = PushshiftAPI()

def get_comments(*args,**kwargs):
  comments_generator = api.search_comments(*args,**kwargs)
  comments = list(comments_generator)
  comments_df = pd.DataFrame(comments)
  return comments_df

def pull_comments(reddit_params,num_workers):
  reddit_sub_results = []
  for comment_params in reddit_params:
    comment_df = get_comments(**comment_params,num_workers=num_workers)
    reddit_sub_results.append(comment_df)
  comments_df = pd.concat(reddit_sub_results).reset_index(drop=True)
  return comments_df

def find_last_date(subreddit,master_df):
    filter = master_df['subreddit']==subreddit
    df = master_df[filter].set_index('date')\
                          .sort_index()
    last = list(df.index)[-1]
    return last

def generate_reddit_params(subreddits,master_df,since,until,**kwargs):
    reddit_params = []
    for subreddit in subreddits:
        reddit_param = dict(
        since = since if subreddit not in master_df['subreddit'] else pd.to_datetime(find_last_date(subreddit,master_df)) + pd.Timedelta(days=1),
        until = until,
        **kwargs
        )
        reddit_params.append(reddit_param)
    return reddit_params

class comment_generator:
    def __init__(self,subreddits,master_comments_df_path,start,end):
        self.master_comments_df_path = master_comments_df_path
        self.subreddits = subreddits
        self.master_db = pd.read_csv(master_comments_df_path,index_col=0)
        self.start = start
        self.end = end

    def comments(self,num_workers):
        reddit_params = generate_reddit_params(self.subreddits,self.master_db,self.start,self.end)
        comments = pull_comments(reddit_params,num_workers)
        print(comments)
        comments['date'] = pd.to_datetime(comments['utc_datetime_str']).dt.to_period('D')
        self.master_db = pd.concat([self.master_db,comments])
        self.master_db.sort_values(by=['subreddit','date'],inplace=True)
        self.master_db.to_csv(self.master_comments_df_path)

if __name__=="__main__":
    subreddits = ['finance']
    # subreddits = ['CryptoCurrency','Bitcoin','Economics','StockMarket','stocks','investing','finance','personalfinance']
    master_comments_db_path = '/Users/brianpisaneschi/Library/CloudStorage/GoogleDrive-pisaneschi.brian.m@gmail.com/My Drive/Data Repos/Reddit/master_comments_db.csv'
    start = '2022-11-04'
    end = dt.today() + pd.Timedelta(days=1)
    generate = comment_generator(subreddits,master_comments_db_path,start,end)
    generate.comments(4)

    


       





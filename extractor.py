import pandas as pd
from pmaw import PushshiftAPI 
from datetime import datetime as dt

api = PushshiftAPI()

def get_comments(*args,**kwargs):
    comments_generator = api.search_comments(*args,**kwargs)
    comments = list(comments_generator)
    comments_df = pd.DataFrame(comments)
    return comments_df

def set_dtypes(comments_df,**kwargs):
    dtypes = kwargs['dtypes'] 
    comments_df = comments_df.astype(dtypes)
    comments_df = comments_df.replace({'None':None,'NaN':None})
    return comments_df

def pull_comments(reddit_params,num_workers,keep_cols,**kwargs):
    subreddits = kwargs['subreddits']
    reddit_sub_results = []
    for comment_params in reddit_params:
        comment_df = get_comments(**comment_params,num_workers=num_workers)
        reddit_sub_results.append(comment_df)
    comments_df = pd.concat(reddit_sub_results).reset_index(drop=True)
    if comments_df.empty:
      return comments_df
    else:
      filter = comments_df['subreddit'].isin(subreddits)
      comments_df = comments_df.loc[filter,keep_cols]
      comments_df.loc[:,'date'] = pd.to_datetime(comments_df['utc_datetime_str']).dt.to_period('D')
      comments_df.loc[:,'utc_datetime'] = pd.to_datetime(comments_df['utc_datetime_str'])
      return set_dtypes(comments_df,**kwargs)

def find_last_date(subreddit,master_df):
    filter = master_df['subreddit']==subreddit
    df = master_df[filter].set_index('date')\
                          .sort_index()
    last = list(df.index)[-1]
    return last.to_timestamp()

def generate_reddit_params(subreddits,master_df,since,until,**kwargs):
    reddit_params = []
    for subreddit in subreddits:
        reddit_param = dict(
        subreddit = subreddit,
        since = int((pd.to_datetime(find_last_date(subreddit,master_df),unit='s') + pd.Timedelta(days=1)).timestamp()) if subreddit in list(master_df['subreddit']) else since,
        until = until,
        **kwargs
        )
        reddit_params.append(reddit_param)
    return reddit_params

class comment_generator:
    def __init__(self,subreddits,master_comments_df_path,start,end):
        self.master_comments_df_path = master_comments_df_path
        self.subreddits = subreddits
        self.master_db = pd.read_feather(master_comments_df_path)
        self.start = start
        self.end = end
        self.dtypes = {'subreddit_id':str,'subreddit':str,'parent_id':float,'id':str,'author':str,'author_fullname':str,'parent_id':float,'body':str,'is_submitter':bool,'permalink':str,'controversiality':float,'distinguished':str,'utc_datetime_str':str,'date':'period[D]','utc_datetime':'datetime64'}
        self.keep_cols = keep_cols = ['subreddit_id','subreddit','id','author','author_fullname','parent_id','body','is_submitter','permalink','controversiality','distinguished','utc_datetime_str']

    def comments(self,num_workers):
        reddit_params = generate_reddit_params(self.subreddits,self.master_db,self.start,self.end)
        comments = pull_comments(reddit_params,num_workers,dtypes=self.dtypes,keep_cols=self.keep_cols,subreddits=self.subreddits)
        if comments.empty:    
          print('No comments were pulled for the dates requested')
          pass
        else:
          self.master_db = pd.concat([self.master_db,comments])
          self.master_db.sort_values(by=['subreddit','date'],inplace=True)
          self.master_db.reset_index(drop=True,inplace=True)
          self.master_db.to_feather(self.master_comments_df_path)

if __name__=="__main__":
    subreddits = ['CryptoCurrency','Bitcoin','Economics','StockMarket','stocks','investing','finance','personalfinance']
    master_comments_db_path = '/content/drive/MyDrive/Data Repos/Reddit/master_comments_db.feather'
    start = int(pd.to_datetime('2022-11-04').timestamp())
    end = int((dt.today() + pd.Timedelta(days=1)).timestamp())
    generate = comment_generator(subreddits,master_comments_db_path,start,end)
    generate.comments(20)
    


       





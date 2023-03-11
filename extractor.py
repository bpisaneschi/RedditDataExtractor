import pandas as pd
from pmaw import PushshiftAPI 
from datetime import datetime as dt
import re
import emoji
from transformers import RobertaForSequenceClassification, RobertaTokenizer
from transformers import pipeline


api = PushshiftAPI()

def process_text(texts):
    texts = str(texts)
    # remove URLs
    texts = re.sub(r'https?://\S+', "", texts)
    texts = re.sub(r'www.\S+', "", texts)
    # remove '
    texts = texts.replace('&#39;', "'")
    # remove symbol names
    texts = re.sub(r'(\#)(\S+)', r'hashtag_\2', texts)
    texts = re.sub(r'(\$)([A-Za-z]+)', r'cashtag_\2', texts)
    # remove usernames
    texts = re.sub(r'(\@)(\S+)', r'mention_\2', texts)
    # demojize
    texts = emoji.demojize(texts, delimiters=("", " "))
    return texts.strip()

def filter_process_comments(comments_df,remove_list):
    replace_dict = {'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&apos;':"'",'\n': ' '}
    filter = (comments_df['body'].str.lower().str.contains('|'.join(remove_list))) & (comments_df['body'].str.lower() == '[deleted]')
    comments_df_filtered = comments_df[~filter]
    comments_df_filtered['body'].replace(replace_dict,inplace=True,regex=True)
    comments_df_filtered['body'] = comments_df_filtered['body'].apply(lambda x: process_text(x))
    return comments_df_filtered

def get_comments(*args,**kwargs):
    print(f'subreddit:{kwargs["subreddit"]} since:{pd.to_datetime(kwargs["since"],unit="s")} until:{pd.to_datetime(kwargs["until"],unit="s")}')
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
        comments_df.loc[:,'date'] = pd.to_datetime(comments_df['utc_datetime_str']).dt.date
        comments_df.loc[:,'utc_datetime'] = pd.to_datetime(comments_df['utc_datetime_str'])
        return set_dtypes(comments_df,**kwargs)

def find_first_last_date(subreddit,master_df):
    filter = master_df['subreddit']==subreddit
    df = master_df[filter].sort_values(by='date')
    first = list(df.utc_datetime)[0]
    last = list(df.utc_datetime)[-1]
    return int(first.timestamp()), int(last.timestamp())

def generate_subreddit_params(subreddit,master_df,since,until,**kwargs):
    if subreddit in list(master_df['subreddit']):
        first, last = find_first_last_date(subreddit,master_df)
        if first > since:
            param_1 = dict(subreddit=subreddit,since=since,until=first,**kwargs)
            param_2 = dict(subreddit=subreddit,since=last,until=until,**kwargs)
            params = [param_1, param_2]
        else:
            params = [dict(subreddit=subreddit,since=last,until=until,**kwargs)]
    else:
        params = [dict(subreddit=subreddit,since=since,until=until,**kwargs)]
    return params
        
def generate_reddit_params(subreddits,master_df,since,until,**kwargs):
    reddit_params = []
    for subreddit in subreddits:
        subreddit_params = generate_subreddit_params(subreddit,master_df,since,until,**kwargs)
        reddit_params += subreddit_params
    return reddit_params

class comment_generator:
    def __init__(self,subreddits,master_comments_db_path,master_labeled_db_path,since,until):
        self.master_comments_db_path = master_comments_db_path
        self.master_labeled_db_path = master_labeled_db_path
        self.subreddits = subreddits
        self.master_db = pd.read_feather(master_comments_db_path)
        self.master_labeled_db = pd.read_feather(master_labeled_db_path)
        self.since = since
        self.until = until
        self.dtypes = {'subreddit_id':str,'subreddit':str,'parent_id':float,'id':str,'author':str,'author_fullname':str,'parent_id':float,'body':str,'is_submitter':bool,'permalink':str,'controversiality':float,'distinguished':str,'utc_datetime_str':str,'date':'datetime64','utc_datetime':'datetime64'}
        self.keep_cols = ['subreddit_id','subreddit','id','author','author_fullname','parent_id','body','is_submitter','permalink','controversiality','distinguished','utc_datetime_str']
        self.label_keep_cols = ['id', 'subreddit', 'body', 'utc_datetime', 'date']

    def comments(self,num_workers,remove_list):
        reddit_params = generate_reddit_params(self.subreddits,self.master_db,self.since,self.until)
        comments = pull_comments(reddit_params,num_workers,dtypes=self.dtypes,keep_cols=self.keep_cols,subreddits=self.subreddits)
        if comments.empty:    
            print('No comments were pulled for the dates requested')
            pass
        else:
            self.comments = comments.sort_values(by=['subreddit','date']).reset_index(drop=True)
            self.comments = filter_process_comments(self.comments,remove_list)
            self.master_db = pd.concat([self.master_db,self.comments])\
                                .sort_values(by=['subreddit','date'])\
                                .drop_duplicates(subset='id')\
                                .reset_index(drop=True)
            self.master_db.to_feather(self.master_comments_db_path)

    def filtered_for_seeds(self,seed_words):
        filter = self.comments['body'].str.contains('|'.join(seed_words))
        self.filtered_comments = self.comments.loc[filter,self.label_keep_cols]
        self.master_labeled_db = pd.concat([self.master_labeled_db,self.filtered_comments])\
                                   .drop_duplicates(subset='id')\
                                   .sort_values(by=['subreddit','date'])\
                                   .reset_index(drop=True)
        self.master_labeled_db.to_feather(self.master_labeled_db_path)

    def predictions(self,model):
        filter = self.master_labeled_db.labels.isna()
        labeled_comments = self.master_labeled_db[filter]
        tokenizer_loaded = RobertaTokenizer.from_pretrained(model)
        model_loaded = RobertaForSequenceClassification.from_pretrained(model)
        nlp = pipeline("text-classification", model=model_loaded, tokenizer=tokenizer_loaded)
        sentences = list(labeled_comments['body'].str.lower())
        labels = nlp(sentences,truncation=True)
        labeled_comments.loc[:,'labels'] = [1 if label_dicts['label']=='LABEL_1' else 0 for label_dicts in labels]
        labeled_comments.loc[:,'score'] = [label_dicts['score'] for label_dicts in labels]
        self.master_labeled_db.set_index('id',inplace=True)
        labeled_comments.set_index('id',inplace=True)
        self.master_labeled_db.update(labeled_comments)
        self.master_labeled_db.reset_index(inplace=True)
        self.master_labeled_db.to_feather(self.master_labeled_db_path)

if __name__=="__main__":
    subreddits = ['CryptoCurrency','Bitcoin','Economics','StockMarket','stocks','investing','finance','personalfinance']
    master_comments_db_path = '/content/drive/MyDrive/Data Repos/Reddit/master_comments_db.feather'
    labeled_master_db_path = '/content/drive/MyDrive/Data Repos/Reddit/labeled_comments/bitcoin_w_zhayunduo-roberta-base-stocktwits-finetuned.feather'
    seed_words = ['crypto','bitcoin','ethereum','cryptocurrency','cryptocurrencies','btc','blockchain']
    remove_list = ['i am a bot','your submission has been flagged',]
    model = 'zhayunduo/roberta-base-stocktwits-finetuned'
    since = int(pd.to_datetime('2022-10-20').timestamp())
    until = int((dt.today() + pd.Timedelta(days=1)).timestamp())
    generate = comment_generator(subreddits,master_comments_db_path,labeled_master_db_path,since,until)
    generate.comments(20,remove_list)
    generate.filtered_for_seeds(seed_words)
    generate.predictions(model)
    
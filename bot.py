import tweepy
import praw
import requests
import time
import os
from io import BytesIO
from PIL import Image

class bcolors:
    """Quick class for cleaner shell logs"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class RedditTwitterPipeline():
    """
    A pipeline from Reddit to Twitter:
    - pulls the top five posts from the given subreddit
    - filters posts that've already been tweeted
    - selects posts that have an image or contain Twitter-embeddable URLs.
    - manipulates the text to follow Twitter's character limit
    - posts to Twitter.

    Expects environment variables to contain all secrets.
    """
    def __init__(self, transfer_count=5, subreddit='aww'):
        """Configure the pipeline being connected and the APIs. Environment variables should already be defined."""
        self.subreddit = subreddit
        self.transfer_count = transfer_count

        # Load Reddit authorization
        self.reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'], 
            client_secret=os.environ['REDDIT_CLIENT_SECRET'], 
            user_agent=os.environ['REDDIT_USER_AGENT']
        )

        # Load Twitter authorization
        auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
        auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
        self.twitter = tweepy.API(auth)


    def upload_image(self, image_url, quality=90):
        """Download an image from Reddit and upload to twitter. Return the media ID"""
        image_format = image_url.split('.')[-1]
        image_file = f'latest_image.{image_format}'
        with open(image_file, 'wb') as f:
            f.write(requests.get(image_url).content)

        return self.twitter.media_upload(image_file).media_id
    
    
    def prepare_text(self, reddit_post, embedded=False):
        """Shorten a reddit post's text if necessary, and append the embedded image URL and the subreddit hashtag"""
        reddit_title = str(reddit_post.title)
        reddit_link = reddit_post.shortlink[8:]
        if embedded:
            tweet_text = f'"{reddit_title}" {reddit_link} #{self.subreddit} {reddit_post.url}'
        else:
            tweet_text = f'"{reddit_title}" {reddit_link} #{self.subreddit}'
        if len(tweet_text) > 280:
            shorter = len(tweet_text) - 270
            t_new = reddit_title[:-shorter]
            if embedded:
                return f'"{t_new} ..." {reddit_link} #{self.subreddit} {reddit_post.url}'
            else:
                return f'"{t_new}" {reddit_link} #{self.subreddit}'
        else:
            return tweet_text


    def make_post(self, reddit_post):
        """Post to Twitter and return the new tweet's ID"""
        if reddit_post.url.split('.')[-1] in ['jpg', 'jpeg', 'png']:
            media_id = self.upload_image(reddit_post.url)
            time.sleep(2)
            tweet = self.twitter.update_status(self.prepare_text(reddit_post), media_ids=[media_id])
        else:
            tweet = self.twitter.update_status(self.prepare_text(reddit_post, embedded=True))
        return tweet.id


    def get_new_subs(self, already_tweeted):
        """Get the new submissions, and filter out what we've already tweeted
         and unrecognized file types. Include tweets if Twitter properly embeds
         their URL."""

        all_recent_subs = list(self.reddit.subreddit(self.subreddit).hot(limit=self.transfer_count))

        new_subs = [sub for sub in all_recent_subs if (sub.url.split('.')[-1] in ['jpg', 'jpeg', 'png']
                        or any([x in sub.url for x in ['imgur', 'gfycat']])) and sub.id not in already_tweeted]

        already_tweeted += [s.id for s in new_subs]

        return new_subs, already_tweeted


    def run_pipeline(self):
        # Read in the existing reddit IDs
        with open('already_tweeted.txt') as f:
            already_tweeted = [x.strip() for x in f.readlines() if x]

        # Process IDs
        print('Searching Reddit for latest popular posts.')
        subs, already_tweeted = self.get_new_subs(already_tweeted)
        print(f'Tweets in queue: {len(subs)}')
        for sub in subs:
            print(f'\tTweeting Reddit post: {sub.id}')
            try:
                tweet_id = self.make_post(sub)
                print(f'{bcolors.OKGREEN}\t\t✔ Success! Posted tweet ID {tweet_id} {bcolors.ENDC}')
            except Exception as err:
                print(f'{bcolors.FAIL}\t\t✗ There was a problem posting {sub.id}{bcolors.ENDC}')
                print(err)
            if len(subs) != 1:
                print('\t\tSleeping for 60 seconds.')
                time.sleep(60)
            
        # Write out the existing reddit IDs
        print('Writing existing tweets to a file.')
        with open('already_tweeted.txt', 'w') as f:
            f.write('\n'.join(already_tweeted))

if __name__ == '__main__':
    rtp = RedditTwitterPipeline()
    rtp.run_pipeline()

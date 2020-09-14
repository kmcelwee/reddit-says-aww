"""
"""

import tweepy
import praw
import requests
import time
import os
from io import BytesIO
from PIL import Image

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


TRANSFER_COUNT = 5

# Load Reddit authorization
reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'], 
	client_secret=os.environ['REDDIT_CLIENT_SECRET'], 
	user_agent=os.environ['REDDIT_USER_AGENT']
)

# Load Twitter authorization
auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
twitter = tweepy.API(auth)


def upload_image(image_url, quality=90):
	"""
	"""

	image_format = image_url.split('.')[-1]
	image_file = 'latest_image.' + image_format
	with open(image_file, 'wb') as f:
		f.write(requests.get(image_url).content)

	images = [Image.open(image_file).convert('RGB')] if 'png' in image_url else [Image.open(image_file)]
	
	media_ids = []
	for image in images:
		img_io = BytesIO()

		image.save(img_io, 'jpeg', quality=quality)
		filename = "temp." + image_format
		img_io.seek(0)

		upload_res = twitter.media_upload(filename, file=img_io)
		media_ids.append(upload_res.media_id)

	return media_ids


def prepare_text(reddit_post, embedded=False):
	t = str(reddit_post.title)
	l = reddit_post.shortlink[8:]
	if embedded:
		r_text = '"' + t + '" ' + l + ' #aww ' + reddit_post.url
	else:
		r_text = '"' + t + '" ' + l + ' #aww'
	if len(r_text) > 280:
		shorter = len(r_text) - 270
		t_new = t[:-shorter]
		if embedded:
			return '"' + t_new + '..." ' + l + ' #aww ' + reddit_post.url
		else:
			return '"' + t_new + '" ' + l + ' #aww'
	else:
		return r_text


def make_post(reddit_post):
	if reddit_post.url.split('.')[-1] in ['jpg', 'jpeg', 'png']:
		media_ids = upload_image(reddit_post.url)
		time.sleep(2)
		tweet = twitter.update_status(prepare_text(reddit_post), media_ids=media_ids)
	else:
		tweet = twitter.update_status(prepare_text(reddit_post, embedded=True))
	return tweet.id


def get_new_subs(already_tweeted):
	all_recent_subs = list(reddit.subreddit('aww').hot(limit=TRANSFER_COUNT))

	new_subs = [sub for sub in all_recent_subs if (sub.url.split('.')[-1] in ['jpg', 'jpeg', 'png']
					or any([x in sub.url for x in ['imgur', 'gfycat']])) and sub.id not in already_tweeted]

	already_tweeted += [s.id for s in new_subs]

	return new_subs, already_tweeted


def run_pipeline():
	# Read in the existing reddit IDs
	with open('already_tweeted.txt') as f:
		already_tweeted = [x.strip() for x in f.readlines() if x]

	# Process IDs
	print('Searching Reddit for latest popular posts.')
	subs, already_tweeted = get_new_subs(already_tweeted)
	print(f'{len(subs)} tweets in queue')
	for sub in subs:
		print(f'\tTweeting Reddit post {sub.id}')
		try:
			tweet_id = make_post(sub)
			print(f'{bcolors.OKGREEN}\t\t✔ Success! Posted tweet ID {tweet_id} {bcolors.ENDC}')
		except Exception as err:
			print(f'{bcolors.FAIL}\t\t✗ There was a problem posting {sub.id}{bcolors.ENDC}')
			print(err)
		print('\t\tSleeping for 60 seconds.')
		time.sleep(60)
	
	# Write out the existing reddit IDs
	print('Writing existing tweets to a file.')
	with open('already_tweeted.txt', 'w') as f:
		f.write('\n'.join(already_tweeted))

if __name__ == '__main__':
	run_pipeline()

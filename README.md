# Reddit Says Aww
A Twitter bot ([@reddit_says_aww](https://twitter.com/reddit_says_aww/)) that brings the top-rated content from the [r/aww](https://www.reddit.com/r/aww) subreddit to Twitter. A standard cron job run by GitHub Actions executes `bot.py` hourly.

To run a similar bot on your own device (perhaps for a different subreddit), you'll need to configure the following environment variables from the [Reddit API](https://www.reddit.com/dev/api/) and [Twitter API](https://developer.twitter.com/en/docs):

```sh
# REDDIT
export REDDIT_CLIENT_SECRET='###'
export REDDIT_CLIENT_ID='###'
export REDDIT_USER_AGENT='app-name/version by your-handle'

# TWITTER
export TWITTER_CONSUMER_KEY='###'
export TWITTER_CONSUMER_SECRET='###'
export TWITTER_ACCESS_TOKEN='###'
export TWITTER_ACCESS_TOKEN_SECRET='###'
```

Create a Python 3.8 environment and run `pip install -r requirements.txt`. You should be all set! `python bot.py` will run a single transfer of the top five tweets from the given subreddit.

To run in GitHub Actions, you'll need to [create a personal access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). This allows the Actions workflow to commit to your repo. The `twitter_cron.yml` file looks for this token as a GitHub secret called `SECRET_REPO_TOKEN`. All of the other environment variables listed above will also need to be added as GitHub secrets in order for the process to be automated by GitHub Actions.

However, it's important to note that this solution was developed to handle r/aww's unique challenges. Depending on the format or service, Twitter may or may not embed an image from a link. If you are creating a "Reddit-to-Twitter" bot that is not as dependent on images, I recommend first looking at [IFTT](https://ifttt.com/), which for simpler projects may work just as well.
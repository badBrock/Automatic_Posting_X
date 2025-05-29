from twikit import Client, TooManyRequests
import time
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint

MINIMUM_TWEETS = 10
QUERY = '(from:elonmusk) lang:en'

def get_tweets(client, tweets):
    if tweets is None:
        # Get tweets
        print(f'{datetime.now()} - Getting tweets...')
        tweets = client.search_tweet(QUERY, product='Top')
    else:
        wait_time = randint(5, 10)
        print(f'{datetime.now()} - Getting next tweets after {wait_time} seconds ...')
        time.sleep(wait_time)
        tweets = tweets.next()
    return tweets

# Login credentials
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

# Create a csv file
with open('tweets.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Tweet_count', 'Username', 'Text', 'Created At', 'Retweets', 'Likes'])

# Authenticate to X.com
client = Client(language='en-US')

# Try to load existing cookies first, if that fails, login
try:
    client.load_cookies('cookies.json')
    print("Loaded existing cookies")
except:
    print("No cookies found, logging in...")
    client.login(auth_info_1=username, auth_info_2=email, password=password)
    client.save_cookies('cookies.json')
    print("Logged in and saved cookies")

tweet_count = 0
tweets = None

while tweet_count < MINIMUM_TWEETS:
    try:
        tweets = get_tweets(client, tweets)
    except TooManyRequests as e:
        rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
        print(f'{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}')
        wait_time = rate_limit_reset - datetime.now()
        time.sleep(wait_time.total_seconds())
        continue
    except Exception as e:
        print(f'{datetime.now()} - Error: {e}')
        break

    if not tweets:
        print(f'{datetime.now()} - No more tweets found')
        break

    for tweet in tweets:
        tweet_count += 1
        tweet_data = [
            tweet_count, 
            tweet.user.name, 
            tweet.text, 
            tweet.created_at, 
            tweet.retweet_count, 
            tweet.favorite_count
        ]
        
        with open('tweets.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(tweet_data)
        
        print(f'{datetime.now()} - Tweet {tweet_count}: {tweet.text[:50]}...')

    print(f'{datetime.now()} - Got {tweet_count} tweets so far')

print(f'{datetime.now()} - Done! Got {tweet_count} tweets total')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import datetime

def setup_driver(headless=True):
    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless=new')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize Chrome driver: {e}")
        return None

def smooth_scroll(driver, max_tweets=20, timeout=60):
    scroll_pause_time = 1.5
    start_time = time.time()
    tweet_count = 0
    retries = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
        current_count = len(tweet_elements)

        print(f"🌀 Scrolled... Tweets loaded: {current_count}")

        if current_count > tweet_count:
            tweet_count = current_count
            retries = 0
        else:
            retries += 1

        if tweet_count >= max_tweets or retries >= 5 or time.time() - start_time > timeout:
            break

def scrape_tweets_selenium(username, max_tweets=10, headless=True):
    driver = setup_driver(headless=headless)
    if not driver:
        return []

    tweets = []

    try:
        print(f"🔍 Navigating to @{username}'s profile...")
        url = f'https://x.com/{username}'
        driver.get(url)

        print("⏳ Waiting for page to load...")
        time.sleep(5)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]'))
            )
            print("✅ Profile page loaded successfully")
        except:
            print("❌ Could not load profile page - might be private or blocked")
            return tweets

        print(f"🔄 Scrolling to load at least {max_tweets} tweets...")
        smooth_scroll(driver, max_tweets=max_tweets, timeout=60)

        tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
        print(f"✅ Finished scrolling. Total tweets loaded: {len(tweet_elements)}")

        for i, tweet_element in enumerate(tweet_elements):
            if len(tweets) >= max_tweets:
                break

            try:
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = text_element.text

                try:
                    time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                    tweet_time = time_element.get_attribute('datetime')
                except:
                    tweet_time = "Unknown"

                metrics = {}
                try:
                    like_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="like"]')
                    if like_elements:
                        metrics['likes'] = like_elements[0].get_attribute('aria-label') or ""

                    retweet_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="retweet"]')
                    if retweet_elements:
                        metrics['retweets'] = retweet_elements[0].get_attribute('aria-label') or ""
                except:
                    pass

                if not any(t['text'] == tweet_text for t in tweets):
                    tweets.append({
                        'text': tweet_text,
                        'timestamp': tweet_time,
                        'metrics': metrics,
                        'index': len(tweets) + 1
                    })
                    print(f"✅ Collected tweet {len(tweets)}: {tweet_text[:50]}...")
            except Exception as e:
                print(f"⚠️ Error extracting tweet: {e}")
                continue

        print(f"🎉 Successfully collected {len(tweets)} tweets!")

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        driver.quit()
        print("🔒 Browser closed")

    return tweets

def display_tweets(tweets, username):
    if not tweets:
        print(f"❌ No tweets collected for @{username}")
        return

    print(f"\n🐦 Latest {len(tweets)} tweets from @{username}:")
    print("=" * 80)

    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. Posted: {tweet['timestamp']}")
        print(f"   Text: {tweet['text']}")
        if tweet['metrics']:
            metrics_str = ", ".join(f"{k}: {v}" for k, v in tweet['metrics'].items() if v)
            if metrics_str:
                print(f"   Engagement: {metrics_str}")
        print("-" * 40)

def save_tweets_to_file(tweets, username, filename=None):
    if not filename:
        filename = f"{username}_tweets.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tweets': len(tweets),
                'tweets': tweets
            }, f, indent=2, ensure_ascii=False)
        print(f"💾 Tweets saved to {filename}")
    except Exception as e:
        print(f"❌ Could not save tweets: {e}")

def main():
    print("🚀 Twitter Selenium Scraper")
    print("=" * 50)

    username = "elonmusk"  # change this to desired username
    max_tweets = 10
    headless_mode = True
    save_to_file = True

    print(f"Target: @{username}")
    print(f"Max tweets: {max_tweets}")
    print(f"Headless mode: {headless_mode}")
    print("-" * 50)

    tweets = scrape_tweets_selenium(username, max_tweets, headless_mode)
    display_tweets(tweets, username)

    if save_to_file and tweets:
        save_tweets_to_file(tweets, username)

    print(f"\n✨ Scraping completed! Found {len(tweets)} tweets.")
    if not tweets:
        print("\n💡 Troubleshooting tips:")
        print("1. Try headless_mode = False")
        print("2. Check account privacy or login wall")
        print("3. Try different usernames or test manually")

if __name__ == "__main__":
    main()

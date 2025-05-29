from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def setup_driver(headless=True):
    """Setup Chrome driver with optimal settings for Twitter scraping"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Essential arguments for stability
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection measures
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to initialize Chrome driver: {e}")
        print("💡 Make sure Chrome browser is installed on your system")
        return None

def scrape_tweets_selenium(username, max_tweets=10, headless=True):
    """
    Scrape tweets using Selenium WebDriver
    """
    driver = setup_driver(headless=headless)
    if not driver:
        return []
    
    tweets = []
    
    try:
        print(f"🔍 Navigating to @{username}'s profile...")
        url = f'https://x.com/{username}'
        driver.get(url)
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Check if profile exists and is accessible
        try:
            # Look for the profile header or tweets container
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]'))
            )
            print("✅ Profile page loaded successfully")
        except:
            print("❌ Could not load profile page - might be private or blocked")
            return tweets
        
        # Scroll and collect tweets
        last_height = driver.execute_script("return document.body.scrollHeight")
        tweets_collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 10
        
        print(f"📊 Starting to collect tweets (target: {max_tweets})...")
        
        while tweets_collected < max_tweets and scroll_attempts < max_scroll_attempts:
            # Find tweet elements
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            
            print(f"🔍 Found {len(tweet_elements)} tweet elements on page")
            
            for tweet_element in tweet_elements:
                if tweets_collected >= max_tweets:
                    break
                    
                try:
                    # Extract tweet text
                    text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    tweet_text = text_element.text
                    
                    # Extract timestamp if available
                    try:
                        time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                        tweet_time = time_element.get_attribute('datetime')
                    except:
                        tweet_time = "Unknown"
                    
                    # Extract engagement metrics if available
                    try:
                        metrics = {}
                        
                        # Likes
                        like_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="like"]')
                        if like_elements:
                            like_text = like_elements[0].get_attribute('aria-label') or ""
                            metrics['likes'] = like_text
                        
                        # Retweets
                        retweet_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="retweet"]')
                        if retweet_elements:
                            retweet_text = retweet_elements[0].get_attribute('aria-label') or ""
                            metrics['retweets'] = retweet_text
                            
                    except:
                        metrics = {}
                    
                    # Avoid duplicates
                    tweet_data = {
                        'text': tweet_text,
                        'timestamp': tweet_time,
                        'metrics': metrics,
                        'index': tweets_collected + 1
                    }
                    
                    # Check if we already have this tweet
                    if not any(existing['text'] == tweet_text for existing in tweets):
                        tweets.append(tweet_data)
                        tweets_collected += 1
                        print(f"✅ Collected tweet {tweets_collected}: {tweet_text[:50]}...")
                    
                except Exception as e:
                    print(f"⚠️ Could not extract tweet data: {e}")
                    continue
            
            # Scroll down to load more tweets
            if tweets_collected < max_tweets:
                print("⬇️ Scrolling to load more tweets...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    print(f"📄 No new content loaded (attempt {scroll_attempts}/{max_scroll_attempts})")
                else:
                    scroll_attempts = 0  # Reset if we found new content
                    
                last_height = new_height
        
        print(f"🎉 Successfully collected {len(tweets)} tweets!")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        
    finally:
        driver.quit()
        print("🔒 Browser closed")
    
    return tweets

def display_tweets(tweets, username):
    """Display collected tweets in a nice format"""
    if not tweets:
        print(f"❌ No tweets collected for @{username}")
        return
    
    print(f"\n🐦 Latest {len(tweets)} tweets from @{username}:")
    print("=" * 80)
    
    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. Posted: {tweet['timestamp']}")
        print(f"   Text: {tweet['text']}")
        
        if tweet['metrics']:
            metrics_str = ", ".join([f"{k}: {v}" for k, v in tweet['metrics'].items() if v])
            if metrics_str:
                print(f"   Engagement: {metrics_str}")
        
        print("-" * 40)

def save_tweets_to_file(tweets, username, filename=None):
    """Save tweets to a JSON file"""
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

# === MAIN EXECUTION ===
def main():
    print("🚀 Twitter Selenium Scraper")
    print("=" * 50)
    
    # Configuration
    username = "elonmusk"  # Change this to any username
    max_tweets = 10
    headless_mode = True  # Set to False to see the browser in action
    save_to_file = True
    
    print(f"Target: @{username}")
    print(f"Max tweets: {max_tweets}")
    print(f"Headless mode: {headless_mode}")
    print("-" * 50)
    
    # Scrape tweets
    tweets = scrape_tweets_selenium(username, max_tweets, headless_mode)
    
    # Display results
    display_tweets(tweets, username)
    
    # Save to file if requested
    if save_to_file and tweets:
        save_tweets_to_file(tweets, username)
    
    print(f"\n✨ Scraping completed! Found {len(tweets)} tweets.")
    
    if not tweets:
        print("\n💡 Troubleshooting tips:")
        print("1. Try with headless_mode = False to see what's happening")
        print("2. Check if the profile is public and accessible")
        print("3. Twitter might be blocking automated access")
        print("4. Try a different username")

if __name__ == "__main__":
    main()